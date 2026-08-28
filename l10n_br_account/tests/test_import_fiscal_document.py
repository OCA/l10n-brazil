# Copyright 2026 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields
from odoo.tests.common import tagged

from .common import AccountMoveBRCommon


@tagged("post_install", "-at_install")
class TestImportFiscalDocument(AccountMoveBRCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.document_type_55 = cls.env.ref("l10n_br_fiscal.document_55")
        if "l10n_latam.document.type" in cls.env:
            cls._mirror_latam_document_type()
        cls.fiscal_document_to_import = cls.env["l10n_br_fiscal.document"].create(
            {
                "fiscal_operation_id": cls.env.ref("l10n_br_fiscal.fo_compras").id,
                "document_type_id": cls.document_type_55.id,
                "document_serie": "1",
                "document_number": "4952",
                "document_date": fields.Date.from_string("2026-08-17"),
                "issuer": "partner",
                "partner_id": cls.partner_a.id,
                "fiscal_operation_type": "in",
            }
        )
        cls.fiscal_line_to_import = cls.env["l10n_br_fiscal.document.line"].create(
            {
                "document_id": cls.fiscal_document_to_import.id,
                "name": "Purchase Test",
                "product_id": cls.product_a.id,
                "quantity": 10,
                "price_unit": 38.0,
                "fiscal_operation_type": "in",
                "fiscal_operation_id": cls.env.ref("l10n_br_fiscal.fo_compras").id,
                "fiscal_operation_line_id": cls.env.ref(
                    "l10n_br_fiscal.fo_compras_compras"
                ).id,
            }
        )

    def _import_into_new_vendor_bill(self):
        move_form = (
            self.env["account.move"]
            .sudo()
            .import_fiscal_document(
                self.fiscal_document_to_import, move_type="in_invoice"
            )
        )
        return self.env["account.move"].sudo().browse(move_form.id)

    @classmethod
    def _mirror_latam_document_type(cls):
        fiscal_country = cls.company_data["company"].account_fiscal_country_id
        domain = [
            ("code", "=", cls.document_type_55.code),
            ("country_id", "=", fiscal_country.id),
        ]
        if cls.env["l10n_latam.document.type"].search_count(domain):
            return
        cls.env["l10n_latam.document.type"].create(
            {
                "name": cls.document_type_55.name,
                "code": cls.document_type_55.code,
                "country_id": fiscal_country.id,
                "internal_type": "invoice",
                "doc_code_prefix": "NFe",
            }
        )

    def test_import_into_a_new_vendor_bill(self):
        move = self._import_into_new_vendor_bill()

        self.assertEqual(move.move_type, "in_invoice")
        self.assertEqual(move.fiscal_document_id, self.fiscal_document_to_import)
        self.assertEqual(move.partner_id, self.partner_a)
        self.assertEqual(len(move.invoice_line_ids), 1)
        self.assertEqual(move.invoice_line_ids.product_id, self.product_a)
        self.assertEqual(
            move.amount_total, self.fiscal_document_to_import.fiscal_amount_total
        )

        if "l10n_latam.document.type" in self.env:
            self.assertTrue(move.journal_id.l10n_latam_use_documents)
            self.assertTrue(move.l10n_latam_manual_document_number)
            self.assertEqual(
                move.l10n_latam_document_type_id.code, self.document_type_55.code
            )
            self.assertEqual(
                move.l10n_latam_document_number,
                self.fiscal_document_to_import.document_number,
            )

    def test_imported_line_keeps_the_fiscal_quantity(self):
        move = self._import_into_new_vendor_bill()
        line = move.invoice_line_ids

        self.assertEqual(line.quantity, self.fiscal_line_to_import.quantity)
        self.assertEqual(line.price_unit, self.fiscal_line_to_import.price_unit)
        self.assertEqual(line.price_subtotal, self.fiscal_line_to_import.price_gross)

    def test_imported_payment_term_matches_the_document_total(self):
        move = self._import_into_new_vendor_bill()
        payment_term_lines = move.line_ids.filtered(
            lambda line: line.display_type == "payment_term"
        )

        self.assertEqual(
            sum(payment_term_lines.mapped("credit")),
            self.fiscal_document_to_import.amount_financial_total,
        )

    def _import_document_with_taxes_from_a_file(self):
        document = self.env["l10n_br_fiscal.document"].create(
            {
                "fiscal_operation_id": self.env.ref("l10n_br_fiscal.fo_compras").id,
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
                "fiscal_operation_id": self.env.ref("l10n_br_fiscal.fo_compras").id,
                "fiscal_operation_line_id": self.env.ref(
                    "l10n_br_fiscal.fo_compras_compras"
                ).id,
                # The issuer charged 12% of ICMS, and the tax the import matched
                # has no rate: only the value of the file can be trusted here.
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

    def test_the_importer_does_not_read_its_own_recordset(self):
        """``import_fiscal_document`` is decorated ``@api.model``.

        It used to read ``self.fiscal_operation_id`` to fill the line, and
        ``self`` is empty on every call from the wizard and has more than one
        record when ``button_import_fiscal_document`` runs over a recordset.
        """
        two_moves = self.env["account.move"].sudo().search([], limit=2)
        self.assertEqual(len(two_moves), 2, "the test needs two invoices around")

        move_form = two_moves.import_fiscal_document(
            self.fiscal_document_to_import, move_type="in_invoice"
        )
        move = self.env["account.move"].sudo().browse(move_form.id)

        lines = move.invoice_line_ids.filtered("fiscal_document_line_id")
        self.assertTrue(lines)
        for line in lines:
            self.assertEqual(
                line.fiscal_operation_id,
                line.fiscal_document_line_id.fiscal_operation_id,
            )
