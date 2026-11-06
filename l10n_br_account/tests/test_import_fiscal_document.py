# Copyright 2026 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
from unittest.mock import patch

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests.common import tagged

from .common import AccountMoveBRCommon


@tagged("post_install", "-at_install")
class TestImportFiscalDocument(AccountMoveBRCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.document_type_55 = cls.env.ref("l10n_br_fiscal.document_55")
        if "l10n_latam.document.type" in cls.env:
            # Without a matching l10n_latam.document.type the import leaves
            # l10n_latam_document_type_id empty and the form then raises
            # "l10n_latam_document_type_id is a required field" as soon as the
            # journal uses documents (l10n_latam_invoice_document installed).
            cls._mirror_latam_document_type(cls.document_type_55)
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
        # Let the import without sudo below run with the rights of a regular
        # billing user only.
        cls.env.user.groups_id |= cls.env.ref("account.group_account_invoice")

    @classmethod
    def _mirror_latam_document_type(cls, document_type):
        fiscal_country = cls.company_data["company"].account_fiscal_country_id
        domain = [
            ("code", "=", document_type.code),
            ("country_id", "=", fiscal_country.id),
        ]
        if cls.env["l10n_latam.document.type"].search_count(domain):
            return
        cls.env["l10n_latam.document.type"].create(
            {
                "name": document_type.name,
                "code": document_type.code,
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

    def test_import_without_sudo(self):
        # The very same import as a regular billing user: this only passes
        # because the ir.rule domain override in models/ir_rule.py keys its
        # ormcache on the allow_fiscal_access context (and fills the LATAM
        # fields the same way as the sudo import).
        move_form = self.env["account.move"].import_fiscal_document(
            self.fiscal_document_to_import, move_type="in_invoice"
        )
        move = self.env["account.move"].sudo().browse(move_form.id)
        self.assertEqual(move.move_type, "in_invoice")
        self.assertEqual(move.fiscal_document_id, self.fiscal_document_to_import)

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

    def _import_wizard(self, document):
        if not document.company_id:
            document.company_id = self.env.company
        return self.env["l10n_br_fiscal.document.import.wizard"].create(
            {
                "company_id": document.company_id.id,
                "document_key": document.document_key,
            }
        )

    def test_a_linked_bill_blocks_the_import_confirmation(self):
        document = self.fiscal_document_to_import
        document.document_key = "35200159594315000157550010000000022062777169"
        move = self._vendor_bill_for(document)
        self.assertEqual(move.state, "draft")
        self.assertEqual(move.fiscal_document_id, document)
        before = self.env["account.move"].search_count([])
        with self.assertRaises(UserError) as blocked:
            self._import_wizard(document).with_context(
                lang="en_US"
            ).action_import_and_open_move()
        self.assertIn(
            move.with_context(lang="en_US").display_name, str(blocked.exception)
        )
        self.assertIn("linked", str(blocked.exception))
        self.assertEqual(self.env["account.move"].search_count([]), before)

    def test_a_posted_bill_blocks_the_import_confirmation(self):
        document = self.fiscal_document_to_import
        document.document_key = "35200159594315000157550010000000032062777166"
        move = self._vendor_bill_for(document)
        move.state = "posted"
        before = self.env["account.move"].search_count([])
        with self.assertRaises(UserError) as blocked:
            self._import_wizard(document).with_context(
                lang="en_US"
            ).action_import_and_open_move()
        self.assertIn(
            move.with_context(lang="en_US").display_name, str(blocked.exception)
        )
        self.assertIn("posted", str(blocked.exception))
        self.assertEqual(self.env["account.move"].search_count([]), before)

    def test_an_available_document_passes_the_bill_check(self):
        document = self.fiscal_document_to_import
        document.document_key = "35200159594315000157550010000000042062777163"
        self._import_wizard(document)._check_imported_bill_allowed()
        self.assertFalse(document._vendor_bill_import_block_reason())

    def test_the_wizard_uses_the_env_company_when_the_document_has_none(self):
        document = self.fiscal_document_to_import.copy()
        document.company_id = False
        document.document_key = "35200159594315000157550010000000102062777160"
        wizard = self._import_wizard(document)
        self.assertEqual(document.company_id, self.env.company)
        self.assertEqual(wizard.company_id, self.env.company)

    def test_a_file_without_a_key_is_read_before_the_bill_check(self):
        wizard = self.env["l10n_br_fiscal.document.import.wizard"].create(
            {
                "company_id": self.env.company.id,
                "file": base64.b64encode(b"<xml/>"),
            }
        )
        with patch.object(type(wizard), "_onchange_file", autospec=True) as onchange:
            wizard._check_imported_bill_allowed()
        onchange.assert_called_once()

    def test_a_blocked_inbox_stops_the_wizard_before_the_bill(self):
        inbox_model = self.env.get("l10n_br_fiscal_dfe.document")
        if inbox_model is None:
            self.skipTest("The DF-e inbox is not installed.")
        key = "35200159594315000157550010000000992062777160"
        inbox_model.sudo().create(
            {
                "access_key": key,
                "company_id": self.env.company.id,
                "fiscal_type": "nfe",
                "document_state": "3",
            }
        )
        wizard = self.env["l10n_br_fiscal.document.import.wizard"].create(
            {
                "company_id": self.env.company.id,
                "document_key": key,
                "file": base64.b64encode(b"<nfe/>"),
            }
        )
        with self.assertRaises(UserError) as blocked:
            wizard.with_context(lang="en_US")._check_imported_bill_allowed()
        self.assertEqual(
            str(blocked.exception),
            "This document was cancelled at the source.",
        )
