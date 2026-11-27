# Copyright 2026 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests.common import tagged

from odoo.addons.l10n_br_fiscal.constants.fiscal import DOCUMENT_STATE_CANCEL

from .common import AccountMoveBRCommon


@tagged("post_install", "-at_install")
class TestImportFiscalDocument(AccountMoveBRCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.document_type_55 = cls.env.ref("l10n_br_fiscal.document_55")
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
        # Let the import run with the rights of a regular billing user only.
        cls.env.user.groups_id |= cls.env.ref("account.group_account_invoice")

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

    def test_import_into_a_new_customer_invoice(self):
        """A fiscal document issued by the company becomes a customer invoice."""
        document = self.env["l10n_br_fiscal.document"].create(
            {
                "fiscal_operation_id": self.env.ref("l10n_br_fiscal.fo_venda").id,
                "document_type_id": self.document_type_55.id,
                "document_serie": "1",
                "document_number": "24873",
                "document_date": fields.Date.from_string("2026-01-05"),
                "issuer": "company",
                "partner_id": self.partner_a.id,
                "fiscal_operation_type": "out",
                "imported_document": True,
            }
        )
        self.env["l10n_br_fiscal.document.line"].create(
            {
                "document_id": document.id,
                "name": "Sale Test",
                "product_id": self.product_a.id,
                "fiscal_operation_type": "out",
                "fiscal_operation_id": self.env.ref("l10n_br_fiscal.fo_venda").id,
                "fiscal_operation_line_id": self.env.ref(
                    "l10n_br_fiscal.fo_venda_venda"
                ).id,
            }
        )
        serie = self.env["l10n_br_fiscal.document.serie"].create(
            {
                "name": "Serie 1",
                "code": "1",
                "document_type_id": self.document_type_55.id,
                "company_id": document.company_id.id,
            }
        )
        move_form = (
            self.env["account.move"]
            .sudo()
            .import_fiscal_document(document, move_type="out_invoice")
        )
        move = self.env["account.move"].sudo().browse(move_form.id)

        self.assertEqual(move.move_type, "out_invoice")
        self.assertEqual(move.fiscal_document_id, document)
        self.assertEqual(move.document_serie_id, serie)
        self.assertEqual(move.document_number, "24873")
        self.assertEqual(move.date, move.invoice_date)
        self.assertEqual(move.invoice_line_ids.product_id, self.product_a)

    def test_import_customer_invoice_without_serie_is_refused(self):
        document = self.fiscal_document_to_import.copy(
            {
                "fiscal_operation_id": self.env.ref("l10n_br_fiscal.fo_venda").id,
                "issuer": "company",
                "fiscal_operation_type": "out",
                "document_serie": "987",
            }
        )
        with self.assertRaises(UserError):
            self.env["account.move"].sudo().import_fiscal_document(
                document, move_type="out_invoice"
            )

    def _vendor_bill_for(self, document):
        move_form = (
            self.env["account.move"]
            .sudo()
            .import_fiscal_document(document, move_type="in_invoice")
        )
        return self.env["account.move"].sudo().browse(move_form.id)

    def test_cancelling_an_imported_bill_keeps_the_partner_document(self):
        """A document the supplier issued stays as the source left it."""
        document = self.fiscal_document_to_import
        document.imported_document = True
        move = self._vendor_bill_for(document)
        state_before = document.state_edoc

        self.assertTrue(move._cancel_keeps_fiscal_document())
        move.button_cancel()

        self.assertEqual(move.state, "cancel")
        self.assertEqual(document.state_edoc, state_before)

    def test_cancelling_a_company_document_cancels_the_fiscal_document(self):
        """A document this company issued is still cancelled with the bill."""
        document = self.env["l10n_br_fiscal.document"].create(
            {
                "fiscal_operation_id": self.env.ref("l10n_br_fiscal.fo_venda").id,
                "document_type_id": self.document_type_55.id,
                "document_serie": "1",
                "document_number": "4953",
                "document_date": fields.Date.from_string("2026-08-17"),
                "issuer": "company",
                "partner_id": self.partner_a.id,
                "fiscal_operation_type": "out",
                "imported_document": True,
            }
        )
        self.env["l10n_br_fiscal.document.line"].create(
            {
                "document_id": document.id,
                "name": "Sale Test",
                "product_id": self.product_a.id,
                "fiscal_operation_type": "out",
                "fiscal_operation_id": self.env.ref("l10n_br_fiscal.fo_venda").id,
                "fiscal_operation_line_id": self.env.ref(
                    "l10n_br_fiscal.fo_venda_venda"
                ).id,
            }
        )
        document.document_serie_id = self.env["l10n_br_fiscal.document.serie"].create(
            {
                "name": "Serie 1",
                "code": "1",
                "document_type_id": self.document_type_55.id,
                "company_id": document.company_id.id,
            }
        )
        move = (
            self.env["account.move"]
            .sudo()
            .import_fiscal_document(document, move_type="out_invoice")
        )
        move = self.env["account.move"].sudo().browse(move.id)

        self.assertFalse(move._cancel_keeps_fiscal_document())
        move.button_cancel()

        self.assertEqual(move.state, "cancel")
        self.assertEqual(document.state_edoc, DOCUMENT_STATE_CANCEL)
