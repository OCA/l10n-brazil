# Copyright 2026 - TODAY KMEE - Luis Felipe Mileo <mileo@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests.common import tagged

from .common import AccountMoveBRCommon


@tagged("post_install", "-at_install")
class TestImportFiscalDocument(AccountMoveBRCommon):
    """Import an existing fiscal document into a brand new account.move.

    This is the code path used when the fiscal document exists before its
    invoice: imported XML, DUIMP declarations, service invoices captured
    from a PDF. It differs from button_import_fiscal_document, which
    imports into an existing move and is already covered by
    test_account_move_lc.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.configure_normal_company_taxes()
        cls.company = cls.company_data["company"]

    def _create_fiscal_document(self):
        document = self.env["l10n_br_fiscal.document"].create(
            {
                "company_id": self.company.id,
                "fiscal_operation_id": self.env.ref("l10n_br_fiscal.fo_compras").id,
                "fiscal_operation_type": "in",
                "document_type_id": self.env.ref("l10n_br_fiscal.document_55").id,
                "document_number": "123",
                "document_serie": "1",
                "issuer": "partner",
                "partner_id": self.partner_a.id,
            }
        )
        self.env["l10n_br_fiscal.document.line"].create(
            {
                "document_id": document.id,
                "name": "Import Test",
                "product_id": self.product_a.id,
                "fiscal_operation_id": document.fiscal_operation_id.id,
                "fiscal_operation_line_id": self.env.ref(
                    "l10n_br_fiscal.fo_compras_compras"
                ).id,
                "fiscal_operation_type": "in",
                "quantity": 1,
                "price_unit": 100.0,
            }
        )
        return document

    def test_import_into_a_new_vendor_bill(self):
        """A vendor fiscal document is imported into a new vendor bill."""
        document = self._create_fiscal_document()
        move_form = self.env["account.move"].import_fiscal_document(document)
        move = self.env["account.move"].browse(move_form.id)
        self.assertEqual(move.move_type, "in_invoice")
        self.assertEqual(move.fiscal_document_id, document)
        self.assertEqual(move.partner_id, self.partner_a)
        self.assertEqual(move.document_serie, "1")
        self.assertEqual(len(move.invoice_line_ids), 1)
        self.assertEqual(
            move.invoice_line_ids.fiscal_document_line_id,
            document.fiscal_line_ids,
        )
