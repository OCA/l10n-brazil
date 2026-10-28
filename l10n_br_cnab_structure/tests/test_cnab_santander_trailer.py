# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64

from odoo import fields
from odoo.tests.common import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon

POS_RECORD_TYPE = 7  # zero based index of the record type (position 8)
POS_SEGMENT = 13  # zero based index of the segment code (position 14)
REC_BATCH_TRAILER = "5"
REC_DETAIL = "3"
# "SOMA DOS VALORES": positions 24-41 (18 digits, 2 implied decimals)
TRAILER_SUM = slice(23, 41)


@tagged("post_install", "-at_install")
class TestCnabSantanderTrailer(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        cls.chart_template = "br_oca_generic"
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.company = cls.company_data["company"]
        cls.company.update({"vat": "82688625000152"})
        cls.env.user.company_id = cls.company.id
        cls.partner_a.update({"vat": "45823449000198"})

        bank_santander = cls.env.ref("l10n_br_base.res_bank_033")
        bank_itau = cls.env.ref("l10n_br_base.res_bank_341")
        cls.santander_account = cls.env["res.partner.bank"].create(
            {
                "acc_number": "205040",
                "bra_number": "1030",
                "bank_id": bank_santander.id,
                "company_id": cls.company.id,
                "partner_id": cls.company.partner_id.id,
            }
        )
        cls.santander_journal = cls.env["account.journal"].create(
            {
                "name": "Santander Bank",
                "type": "bank",
                "code": "BNKSA",
                "bank_account_id": cls.santander_account.id,
                "bank_id": bank_santander.id,
            }
        )
        cls.partner_bank = cls.env["res.partner.bank"].create(
            {
                "acc_number": "123456",
                "bra_number": "0001",
                "bank_id": bank_itau.id,
                "partner_id": cls.partner_a.id,
            }
        )
        cls.payment_mode = cls.env["account.payment.mode"].create(
            {
                "bank_account_link": "fixed",
                "name": "TED Santander",
                "company_id": cls.company.id,
                "payment_method_id": cls.env.ref(
                    "l10n_br_account_payment_order.payment_mode_type_cnab240_out"
                ).id,
                "payment_mode_domain": "ted",
                "payment_order_ok": True,
                "fixed_journal_id": cls.santander_journal.id,
                "cnab_processor": "oca_processor",
                "cnab_structure_id": cls.env.ref(
                    "l10n_br_cnab_structure.cnab_santander_240"
                ).id,
                "cnab_payment_way_ids": [
                    (
                        6,
                        0,
                        [
                            cls.env.ref(
                                "l10n_br_cnab_structure.cnab_santander_240_pay_way_41"
                            ).id
                        ],
                    )
                ],
            }
        )

    def _create_invoice(self, amount):
        return self.env["account.move"].create(
            {
                "partner_id": self.partner_a.id,
                "partner_bank_id": self.partner_bank.id,
                "move_type": "in_invoice",
                "ref": f"Test Invoice {amount}",
                "invoice_date": fields.Date.today(),
                "company_id": self.company.id,
                "payment_mode_id": self.payment_mode.id,
                "journal_id": self.company_data["default_journal_purchase"].id,
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product_a.id,
                            "quantity": 1.0,
                            "price_unit": amount,
                        },
                    )
                ],
            }
        )

    def _generate_cnab_lines(self, amounts):
        invoices = self.env["account.move"]
        for amount in amounts:
            invoices |= self._create_invoice(amount)
        invoices.action_post()
        self.env["account.invoice.payment.line.multi"].with_context(
            active_model="account.move", active_ids=invoices.ids
        ).create({}).run()
        payment_order = self.env["account.payment.order"].search(
            [
                ("state", "=", "draft"),
                ("payment_type", "=", "outbound"),
                ("company_id", "=", self.company.id),
            ]
        )
        self.assertEqual(len(payment_order), 1)
        payment_order.draft2open()
        action = payment_order.open2generated()
        attachment = self.env["ir.attachment"].browse(action["res_id"])
        return base64.b64decode(attachment.datas).decode().splitlines()

    def test_payment_batch_trailer_sum(self):
        """The batch trailer must sum the segment A amounts.

        The payment batch has detail lines of segments A and B; only the
        segment A lines carry the amount.
        """
        lines = self._generate_cnab_lines([300.0, 150.0])
        segments = [line[POS_SEGMENT] for line in lines if line[7] == REC_DETAIL]
        self.assertEqual(segments.count("A"), 2)
        self.assertIn("B", segments)
        trailers = [
            line for line in lines if line[POS_RECORD_TYPE] == REC_BATCH_TRAILER
        ]
        self.assertEqual(len(trailers), 1)
        self.assertEqual(trailers[0][TRAILER_SUM], f"{45000:018d}")
