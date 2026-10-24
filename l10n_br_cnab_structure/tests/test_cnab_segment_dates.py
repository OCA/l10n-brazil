# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import timedelta

from odoo import fields
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon

BOLETO_DIGITABLE_LINE = "00190123435678901234356789012343399010000123456"


@tagged("post_install", "-at_install")
class TestCnabSegmentDates(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(
        cls, chart_template_ref="l10n_br_coa_generic.l10n_br_coa_generic_template"
    ):
        super().setUpClass(chart_template_ref=chart_template_ref)
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.company = cls.company_data["company"]
        cls.company.update({"cnpj_cpf": "82688625000152"})
        cls.env.user.company_id = cls.company.id
        cls.partner_a.update({"cnpj_cpf": "45823449000198"})

    def _fields_with_date_source(self):
        return self.env["l10n_br_cnab.line.field"].search(
            [
                ("content_source_field", "in", ("date", "ml_maturity_date")),
                ("sending_dynamic_content", "ilike", "strftime"),
            ]
        )

    def test_date_fields_use_line_date(self):
        """A date field fed by a payment line date must not always send today."""
        date_fields = self._fields_with_date_source()
        self.assertTrue(date_fields)
        for field in date_fields:
            self.assertIn(
                "content",
                field.sending_dynamic_content.replace("time.strftime", ""),
                f"{field.display_name} ignores the line date (always today)",
            )

    def _create_boleto_order(self, bank_xid, prefix, code, **line_vals):
        bank = self.env.ref(bank_xid)
        account = self.env["res.partner.bank"].create(
            {
                "acc_number": "99887",
                "bra_number": "4321",
                "bank_id": bank.id,
                "company_id": self.company.id,
                "partner_id": self.company.partner_id.id,
            }
        )
        journal = self.env["account.journal"].create(
            {
                "name": f"Bank {code}",
                "type": "bank",
                "code": code,
                "bank_account_id": account.id,
                "bank_id": bank.id,
            }
        )
        mode = self.env["account.payment.mode"].create(
            {
                "name": f"Mode {code}",
                "bank_account_link": "fixed",
                "company_id": self.company.id,
                "payment_method_id": self.env.ref(
                    "l10n_br_account_payment_order.payment_mode_type_cnab240_out"
                ).id,
                "payment_mode_domain": "boleto",
                "payment_order_ok": True,
                "fixed_journal_id": journal.id,
                "cnab_structure_id": self.env.ref(
                    f"l10n_br_cnab_structure.{prefix}"
                ).id,
                "cnab_payment_way_ids": [
                    (
                        6,
                        0,
                        [
                            self.env.ref(
                                f"l10n_br_cnab_structure.{prefix}_pay_way_31"
                            ).id
                        ],
                    )
                ],
                "cnab_processor": "oca_processor",
            }
        )
        order = self.env["account.payment.order"].create(
            {
                "payment_mode_id": mode.id,
                "state": "draft",
                "company_id": self.company.id,
                "journal_id": journal.id,
            }
        )
        vals = {
            "order_id": order.id,
            "partner_id": self.partner_a.id,
            "amount_currency": 1234.0,
            "communication": "BOLETO TEST",
            "barcode": BOLETO_DIGITABLE_LINE,
        }
        vals.update(line_vals)
        self.env["account.payment.line"].create(vals)
        return order

    def _assert_segment_j_dates(self, bank_xid, prefix, code):
        pay_date = fields.Date.today() + timedelta(days=5)
        due_date = fields.Date.today() + timedelta(days=10)
        order = self._create_boleto_order(
            bank_xid, prefix, code, date=pay_date, ml_maturity_date=due_date
        )
        line = order.payment_line_ids
        due_field = self.env.ref(
            f"l10n_br_cnab_structure.{prefix}_boleto_segmento_j_92_99"
        )
        pay_field = self.env.ref(
            f"l10n_br_cnab_structure.{prefix}_boleto_segmento_j_145_152"
        )
        self.assertEqual(due_field.output(line)[1], due_date.strftime("%d%m%Y"))
        self.assertEqual(pay_field.output(line)[1], pay_date.strftime("%d%m%Y"))

    def test_itau_segment_j_dates(self):
        self._assert_segment_j_dates(
            "l10n_br_base.res_bank_341", "cnab_itau_240", "BNKI"
        )

    def test_bb_segment_j_dates(self):
        self._assert_segment_j_dates("l10n_br_base.res_bank_001", "cnab_bb_240", "BNKB")

    def test_santander_segment_j_dates(self):
        self._assert_segment_j_dates(
            "l10n_br_base.res_bank_033", "cnab_santander_240", "BNKT"
        )

    def test_sicoob_segment_j_dates(self):
        self._assert_segment_j_dates(
            "l10n_br_base.res_bank_756", "cnab_sicoob_240", "BNKS"
        )
