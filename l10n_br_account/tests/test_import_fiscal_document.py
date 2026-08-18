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
        cls.env["l10n_br_fiscal.document.line"].create(
            {
                "document_id": cls.fiscal_document_to_import.id,
                "name": "Purchase Test",
                "product_id": cls.product_a.id,
                "fiscal_operation_type": "in",
                "fiscal_operation_id": cls.env.ref("l10n_br_fiscal.fo_compras").id,
                "fiscal_operation_line_id": cls.env.ref(
                    "l10n_br_fiscal.fo_compras_compras"
                ).id,
            }
        )

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
        move_form = (
            self.env["account.move"]
            .sudo()
            .import_fiscal_document(
                self.fiscal_document_to_import, move_type="in_invoice"
            )
        )
        move = self.env["account.move"].sudo().browse(move_form.id)

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
