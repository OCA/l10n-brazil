# Copyright 2026 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields
from odoo.tests.common import tagged

from .common import AccountMoveBRCommon


@tagged("post_install", "-at_install")
class TestImportedLineTaxes(AccountMoveBRCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.document_type_55 = cls.env.ref("l10n_br_fiscal.document_55")
        cls.operation = cls.env.ref("l10n_br_fiscal.fo_compras")
        cls.operation_line = cls.env.ref("l10n_br_fiscal.fo_compras_compras")

    def _import_document_with_taxes_from_a_file(self):
        document = self.env["l10n_br_fiscal.document"].create(
            {
                "fiscal_operation_id": self.operation.id,
                "document_type_id": self.document_type_55.id,
                "document_serie": "1",
                "document_number": "4953",
                "document_date": fields.Date.from_string("2026-08-17"),
                "issuer": "partner",
                "partner_id": self.partner_a.id,
                "fiscal_operation_type": "in",
                "imported_document": True,
            }
        )
        self.env["l10n_br_fiscal.document.line"].create(
            {
                "document_id": document.id,
                "name": "Imported purchase line",
                "product_id": self.product_a.id,
                "quantity": 39,
                "price_unit": 100.0,
                "fiscal_operation_type": "in",
                "fiscal_operation_id": self.operation.id,
                "fiscal_operation_line_id": self.operation_line.id,
                "icms_tax_id": self.env.ref("l10n_br_fiscal.tax_icms_nt").id,
                "icms_base": 3900.0,
                "icms_percent": 12.0,
                "icms_value": 468.0,
                "ipi_tax_id": self.env.ref("l10n_br_fiscal.tax_ipi_6_5").id,
                "ipi_base": 3900.0,
                "ipi_percent": 9.75,
                "ipi_value": 380.25,
            }
        )
        move_form = (
            self.env["account.move"]
            .sudo()
            .import_fiscal_document(document, move_type="in_invoice")
        )
        return document, self.env["account.move"].sudo().browse(move_form.id)

    def test_the_tax_lines_carry_the_values_of_the_file(self):
        _document, move = self._import_document_with_taxes_from_a_file()
        tax_lines = move.line_ids.filtered(lambda line: line.display_type == "tax")
        tax_amounts = {
            line.tax_line_id.tax_group_id.fiscal_tax_group_id.tax_domain: line.debit
            for line in tax_lines
        }

        self.assertEqual(tax_amounts, {"icms": 468.0, "ipi": 380.25})

    def test_the_payment_term_of_an_imported_document_matches_the_file(self):
        document, move = self._import_document_with_taxes_from_a_file()
        payment_term_lines = move.line_ids.filtered(
            lambda line: line.display_type == "payment_term"
        )

        self.assertEqual(sum(payment_term_lines.mapped("credit")), 4280.25)
        self.assertEqual(document.amount_financial_total, 4280.25)
