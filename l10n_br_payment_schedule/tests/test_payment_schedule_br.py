# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import timedelta

from brbank.instrumento import crc16_ccitt, linha_digitavel_do_codigo

from odoo import fields
from odoo.exceptions import ValidationError
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.addons.base.tests.common import DISABLED_MAIL_CONTEXT

# Public test data of the Banco do Brasil homologation environment.
BOLETO = "00195313800000015000000003051284190526000117"
GUIA = "83630000000641400052836100812355200812351310"
# Fictitious CNPJs, checked not to belong to any company.
CNPJ_PARTNER = "91300766000147"
CNPJ_OTHER = "98016373000155"


def brcode(key=None, url=None, amount=None):
    account = "0014br.gov.bcb.pix"
    if key:
        account += f"01{len(key):02d}{key}"
    if url:
        account += f"25{len(url):02d}{url}"
    text = f"00020126{len(account):02d}{account}520400005303986"
    if amount:
        text += f"54{len(amount):02d}{amount}"
    text += "5802BR5913EMPRESA TESTE6009SAO PAULO62070503***6304"
    return text + crc16_ccitt(text)


@tagged("-at_install", "post_install")
class TestPaymentScheduleBr(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls, chart_template_ref=None):
        super().setUpClass(chart_template_ref=chart_template_ref)
        cls.env = cls.env(context=dict(cls.env.context, **DISABLED_MAIL_CONTEXT))
        cls.today = fields.Date.context_today(cls.env.user)
        cls.partner_a.cnpj_cpf = CNPJ_PARTNER
        mode_model = cls.env["account.payment.mode"]
        cls.modes = {
            kind: mode_model.create(
                {
                    "name": f"Pay by {kind}",
                    "company_id": cls.company_data["company"].id,
                    "bank_account_link": "fixed",
                    "fixed_journal_id": cls.company_data["default_journal_bank"].id,
                    "payment_method_id": cls.env.ref(
                        "account.account_payment_method_manual_out"
                    ).id,
                    "payment_mode_domain": kind,
                }
            )
            for kind in ("boleto", "pix_transfer", "ted")
        }

    def _item(self, kind, amount=15.0):
        bill = self.env["account.move"].create(
            {
                "move_type": "in_invoice",
                "partner_id": self.partner_a.id,
                "ref": f"NF-{kind}-{amount}",
                "invoice_payment_term_id": False,
                "invoice_date": self.today,
                "invoice_date_due": self.today + timedelta(days=2),
                "payment_mode_id": self.modes[kind].id,
                "invoice_line_ids": [
                    (0, 0, {"name": "Service", "price_unit": amount, "tax_ids": []})
                ],
            }
        )
        bill.action_post()
        return bill.line_ids.filtered(
            lambda line: line.account_type == "liability_payable"
        )

    def _assert_state(self, line, state):
        self.assertEqual(line.payment_schedule_state, state)
        found = self.env["account.move.line"].search(
            [("id", "=", line.id), ("payment_schedule_state", "=", state)]
        )
        self.assertEqual(found, line, f"search and compute disagree on {state}")

    def test_boleto_needs_a_valid_barcode(self):
        line = self._item("boleto")
        self._assert_state(line, "missing_instrument")
        with self.assertRaises(ValidationError):
            line.payment_barcode = BOLETO[:4] + "0" + BOLETO[5:]
        line.payment_barcode = linha_digitavel_do_codigo(BOLETO)
        self.assertEqual(line.payment_barcode, BOLETO)
        self.assertEqual(line.payment_barcode_type, "boleto")
        self.assertEqual(line.payment_digitable_line, linha_digitavel_do_codigo(BOLETO))
        self._assert_state(line, "to_schedule")
        order = line._payment_schedule_create_orders()
        self.assertEqual(order.payment_line_ids.barcode, BOLETO)

    def test_guia(self):
        line = self._item("boleto", 64.14)
        line.payment_barcode = GUIA
        self.assertEqual(line.payment_barcode_type, "guia")
        self._assert_state(line, "to_schedule")

    def test_pix_receiver(self):
        line = self._item("pix_transfer")
        self._assert_state(line, "missing_instrument")
        own = self.env["res.partner.pix"].create(
            {
                "partner_id": self.partner_a.id,
                "key_type": "cnpj_cpf",
                "key": CNPJ_PARTNER,
            }
        )
        line.partner_pix_id = own
        self.assertEqual(line.payment_pix_check, "checked")
        self._assert_state(line, "to_schedule")
        order = line._payment_schedule_create_orders()
        self.assertEqual(order.payment_line_ids.partner_pix_id, own)

    def test_pix_copy_paste_of_someone_else(self):
        line = self._item("pix_transfer")
        line.payment_pix_copy_paste = brcode(key=CNPJ_OTHER)
        self.assertEqual(line.payment_pix_check, "mismatch")
        self._assert_state(line, "missing_instrument")
        with self.assertRaises(ValidationError):
            line.payment_pix_copy_paste = "not a pix code"

    def test_pix_other_keys_and_dynamic_qr_are_to_check(self):
        line = self._item("pix_transfer")
        line.payment_pix_copy_paste = brcode(url="pix.example.com/qr/v2/abc")
        self.assertEqual(line.payment_pix_check, "to_check")
        email = self.env["res.partner.pix"].create(
            {
                "partner_id": self.partner_a.id,
                "key_type": "email",
                "key": "pay@example.com",
            }
        )
        line.write({"payment_pix_copy_paste": False, "partner_pix_id": email.id})
        self.assertEqual(line.payment_pix_check, "to_check")
        self._assert_state(line, "to_schedule")

    def test_pix_and_ted_by_bank_account(self):
        pix = self._item("pix_transfer")
        ted = self._item("ted")
        self._assert_state(pix, "missing_instrument")
        self._assert_state(ted, "missing_instrument")
        bank = self.env["res.partner.bank"].create(
            {
                "partner_id": self.partner_a.id,
                "acc_number": "60840",
                "acc_number_dig": "8",
                "bra_number": "1607",
                "bank_id": self.env["res.bank"]
                .create({"name": "Test Bank", "code_bc": "999"})
                .id,
            }
        )
        (pix | ted).invalidate_recordset(["payment_schedule_state"])
        self._assert_state(ted, "to_schedule")
        self._assert_state(pix, "missing_instrument")
        bank.transactional_acc_type = "checking"
        pix.invalidate_recordset(["payment_schedule_state"])
        self._assert_state(pix, "to_schedule")

    def _reader(self, line, text):
        return self.env["l10n_br_payment_schedule.instrument.reader"].create(
            {"move_line_id": line.id, "text": text}
        )

    def test_reader_barcode(self):
        line = self._item("boleto", 15.0)
        reader = self._reader(line, linha_digitavel_do_codigo(BOLETO))
        self.assertEqual(reader.kind, "barcode")
        self.assertFalse(reader.message)
        reader.action_apply()
        self.assertEqual(line.payment_barcode, BOLETO)
        other = self._item("boleto", 20.0)
        self.assertTrue(self._reader(other, BOLETO).message)
        self.assertTrue(self._reader(other, "123").error)

    def test_reader_pix_registers_key_on_request(self):
        line = self._item("pix_transfer", 12.5)
        reader = self._reader(line, brcode(key=CNPJ_PARTNER, amount="12.50"))
        self.assertEqual(reader.kind, "pix")
        self.assertEqual(reader.pix_key, CNPJ_PARTNER)
        self.assertFalse(reader.pix_key_id)
        self.assertFalse(reader.message)
        self.assertFalse(self.partner_a.pix_key_ids)
        reader.action_register_pix_key()
        reader.invalidate_recordset()
        self.assertEqual(reader.pix_key_id.key, CNPJ_PARTNER)
        reader.action_apply()
        self.assertEqual(line.partner_pix_id, reader.pix_key_id)
        self.assertEqual(line.payment_pix_check, "checked")
        self._assert_state(line, "to_schedule")
