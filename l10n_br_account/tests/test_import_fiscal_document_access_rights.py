# Copyright 2026 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields
from odoo.tests.common import tagged

from .common import AccountMoveBRCommon


@tagged("post_install", "-at_install")
class TestImportFiscalDocumentAccessRights(AccountMoveBRCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.user.groups_id |= cls.env.ref("account.group_account_invoice")
        cls._mirror_latam_document_type()
        cls.fiscal_document_to_import = cls.env["l10n_br_fiscal.document"].create(
            {
                "fiscal_operation_id": cls.env.ref("l10n_br_fiscal.fo_compras").id,
                "document_type_id": cls.env.ref("l10n_br_fiscal.document_55").id,
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
        if "l10n_latam.document.type" not in cls.env:
            return
        document_type = cls.env.ref("l10n_br_fiscal.document_55")
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

    def test_import_without_sudo(self):
        move_form = self.env["account.move"].import_fiscal_document(
            self.fiscal_document_to_import, move_type="in_invoice"
        )
        move = self.env["account.move"].sudo().browse(move_form.id)
        self.assertEqual(move.move_type, "in_invoice")
        self.assertEqual(move.fiscal_document_id, self.fiscal_document_to_import)
