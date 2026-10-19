# Copyright (C) 2026 Madooit
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import Command
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestDownPaymentFiscalLines(TransactionCase):
    """Check the fiscal line linkage of the down payment deduction lines.

    On a final invoice the sale module inserts a "Down Payments" section
    before the deduction lines. The deduction lines carry a fiscal operation
    but no fiscal operation line. Since account.move.line._inherits creates
    the fiscal document lines positionally, the create override must reorder
    the lines with the same criterion used by the fiscal document line
    create filter. Otherwise the fiscal lines are shifted and the down
    payment lines are left without their fiscal line.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.company = cls.env.ref("l10n_br_base.empresa_lucro_presumido")
        cls.env.user.company_ids = [Command.set(cls.company.ids)]
        cls.env.user.company_id = cls.company
        cls.partner = cls.env.ref("l10n_br_base.res_partner_cliente5_pe")
        cls.fiscal_operation = cls.env.ref("l10n_br_fiscal.fo_venda")
        cls.income_account = cls.env["account.account"].create(
            {
                "company_ids": [Command.set(cls.company.ids)],
                "account_type": "income",
                "code": "705071",
                "name": "Down payment revenue (test)",
            }
        )
        cls.move = cls.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "company_id": cls.company.id,
                "partner_id": cls.partner.id,
                "fiscal_operation_id": cls.fiscal_operation.id,
                "document_type_id": cls.env.ref("l10n_br_fiscal.document_55").id,
                "document_serie_id": cls.env.ref(
                    "l10n_br_fiscal.empresa_lc_document_55_serie_1"
                ).id,
            }
        )

    def test_down_payment_fiscal_line_is_not_shifted(self):
        self.assertTrue(self.move.fiscal_document_id)
        self.move.write(
            {
                "invoice_line_ids": [
                    # The sale module inserts a "Down Payments" section
                    # before the deduction lines.
                    Command.create(
                        {
                            "display_type": "line_section",
                            "name": "Down Payments",
                        }
                    ),
                    Command.create(
                        {
                            "name": "Down payment",
                            "quantity": 1.0,
                            "price_unit": -4000.0,
                            "account_id": self.income_account.id,
                            "fiscal_operation_id": self.fiscal_operation.id,
                            # A down payment line has no operation line.
                            "fiscal_operation_line_id": False,
                        }
                    ),
                ]
            }
        )
        section = self.move.invoice_line_ids.filtered(
            lambda line: line.display_type == "line_section"
        )
        down_payment = self.move.invoice_line_ids.filtered(
            lambda line: line.display_type == "product"
        )
        self.assertEqual(len(section), 1)
        self.assertEqual(len(down_payment), 1)
        self.assertFalse(section.fiscal_document_line_id)
        self.assertTrue(down_payment.fiscal_document_line_id)
        self.assertEqual(
            down_payment.fiscal_document_line_id.fiscal_operation_id,
            self.fiscal_operation,
        )
