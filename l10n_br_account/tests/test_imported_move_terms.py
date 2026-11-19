# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import Command, fields
from odoo.tests import tagged

from .common import AccountMoveBRCommon


@tagged("post_install", "-at_install")
class TestImportedMoveTerms(AccountMoveBRCommon):
    @classmethod
    def setUpClass(cls, chart_template_ref=None):
        super().setUpClass(chart_template_ref=chart_template_ref)
        # the NF-e installments model is read when l10n_br_account_nfe is installed
        nfe_manager = cls.env.ref("l10n_br_nfe.group_manager", False)
        if nfe_manager:
            cls.env.user.groups_id |= nfe_manager
        cls.company = cls.env.company
        cls.partner = cls.partner_a
        cls.operation = cls.env.ref("l10n_br_fiscal.fo_compras")
        cls.operation_line = cls.env.ref("l10n_br_fiscal.fo_compras_compras")
        cls.product = cls.env["product.product"].create(
            {"name": "Imported service", "type": "service"}
        )
        cls.payment_term = cls.env["account.payment.term"].create(
            {
                "name": "Two installments",
                "line_ids": [
                    Command.create(
                        {"value": "percent", "value_amount": 50.0, "days": 30}
                    ),
                    Command.create(
                        {"value": "balance", "value_amount": 0.0, "days": 60}
                    ),
                ],
            }
        )

    def _import_move(self, tax_values=None, payment_term=None):
        line_values = {
            "name": "Imported line",
            "product_id": self.product.id,
            "uom_id": self.product.uom_id.id,
            "quantity": 1,
            "price_unit": 1000.0,
            "fiscal_operation_type": "in",
            "fiscal_operation_id": self.operation.id,
            "fiscal_operation_line_id": self.operation_line.id,
        }
        line_values.update(tax_values or {})
        document = self.env["l10n_br_fiscal.document"].create(
            {
                "company_id": self.company.id,
                "document_type_id": self.env.ref("l10n_br_fiscal.document_SE").id,
                "document_serie": "1",
                "document_number": "100",
                "issuer": "partner",
                "partner_id": self.partner.id,
                "fiscal_operation_id": self.operation.id,
                "fiscal_operation_type": "in",
                "document_date": "2026-01-10 12:00:00",
                "imported_document": True,
                "fiscal_line_ids": [Command.create(line_values)],
            }
        )
        form = self.env["account.move"].import_fiscal_document(document)
        move = self.env["account.move"].browse(form.id)
        move.invoice_payment_term_id = payment_term
        return move

    def _wh_taxes(self):
        return {
            "issqn_wh_tax_id": self.env.ref("l10n_br_fiscal.tax_issqn_wh_5").id,
            "issqn_wh_base": 1000.0,
            "issqn_wh_percent": 5.0,
            "issqn_wh_value": 50.0,
            "pis_wh_tax_id": self.env.ref("l10n_br_fiscal.tax_pis_wh_0_65").id,
            "pis_wh_base": 1000.0,
            "pis_wh_percent": 0.65,
            "pis_wh_value": 6.5,
            "cofins_wh_tax_id": self.env.ref("l10n_br_fiscal.tax_cofins_wh_3").id,
            "cofins_wh_base": 1000.0,
            "cofins_wh_percent": 3.0,
            "cofins_wh_value": 30.0,
            "csll_wh_tax_id": self.env.ref("l10n_br_fiscal.tax_csll_wh_1").id,
            "csll_wh_base": 1000.0,
            "csll_wh_percent": 1.0,
            "csll_wh_value": 10.0,
        }

    def _assert_balanced(self, move):
        self.assertAlmostEqual(sum(move.line_ids.mapped("balance")), 0.0, places=2)

    def test_payment_term_applies_when_no_installment_is_declared(self):
        move = self._import_move(payment_term=self.payment_term)
        self.assertTrue(move.imported_document)
        self._assert_balanced(move)
        due_lines = move.line_ids.filtered(
            lambda line: line.display_type == "payment_term"
        ).sorted("date_maturity")
        self.assertEqual(
            due_lines.mapped("date_maturity"),
            [
                fields.Date.to_date("2026-02-09"),
                fields.Date.to_date("2026-03-11"),
            ],
        )
        self.assertAlmostEqual(sum(due_lines.mapped("credit")), 1000.0, places=2)
        self.assertAlmostEqual(due_lines[0].credit, 500.0, places=2)

    def test_single_due_date_when_there_is_no_payment_term(self):
        move = self._import_move()
        self._assert_balanced(move)
        due_lines = move.line_ids.filtered(
            lambda line: line.display_type == "payment_term"
        )
        self.assertEqual(len(due_lines), 1)
        self.assertEqual(due_lines.date_maturity, move.invoice_date_due)
        self.assertAlmostEqual(due_lines.credit, 1000.0, places=2)

    def test_withholdings_of_the_document_reduce_the_amount_to_pay(self):
        move = self._import_move(self._wh_taxes())
        self._assert_balanced(move)
        due_lines = move.line_ids.filtered(
            lambda line: line.display_type == "payment_term"
        )
        self.assertAlmostEqual(sum(due_lines.mapped("credit")), 903.5, places=2)
        withheld = move.line_ids.filtered(
            lambda line: line.display_type == "tax"
            and line.tax_line_id.tax_group_id.fiscal_tax_group_id.tax_withholding
        )
        self.assertEqual(len(withheld), 4)
        self.assertAlmostEqual(sum(withheld.mapped("balance")), -96.5, places=2)
        self.assertAlmostEqual(move.amount_total, 903.5, places=2)

    def test_document_without_withholding_is_untouched(self):
        move = self._import_move()
        self._assert_balanced(move)
        withheld = move.line_ids.filtered(
            lambda line: line.display_type == "tax"
            and line.tax_line_id.tax_group_id.fiscal_tax_group_id.tax_withholding
        )
        self.assertFalse(withheld)
        self.assertAlmostEqual(move.amount_total, 1000.0, places=2)

    def test_withheld_value_without_withholding_tax_is_not_discounted(self):
        """A withheld value whose domain has no withholding tax in the line
        generates no tax line, so it must stay in the amount to pay."""
        tax_values = {
            "issqn_wh_tax_id": self.env.ref("l10n_br_fiscal.tax_issqn_wh_5").id,
            "issqn_wh_base": 1000.0,
            "issqn_wh_percent": 5.0,
            "issqn_wh_value": 50.0,
            "pis_wh_base": 1000.0,
            "pis_wh_percent": 0.65,
            "pis_wh_value": 6.5,
        }
        move = self._import_move(tax_values, payment_term=self.payment_term)
        self._assert_balanced(move)
        due_lines = move.line_ids.filtered(
            lambda line: line.display_type == "payment_term"
        )
        self.assertEqual(len(due_lines), 2)
        self.assertAlmostEqual(sum(due_lines.mapped("credit")), 950.0, places=2)
