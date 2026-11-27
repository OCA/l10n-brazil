# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import importlib.util
import os
from unittest.mock import patch

from odoo.modules.module import get_module_path
from odoo.tests.common import TransactionCase

from odoo.addons.l10n_br_nfse_dfe.tests.test_nfse_dfe import nfse_xml

XMLID_NAME = "field_res_company__nfse_import_product_id"


class TestNfseImportMigration(TransactionCase):
    """The DANFSE of an imported NFS-e, and the field that moved to l10n_br_nfse."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.ref("l10n_br_base.empresa_lucro_presumido")
        cls.Document = cls.env["l10n_br_fiscal.document"]

    def test_the_danfse_of_an_imported_nfse_is_printed_from_the_original_xml(self):
        documents, errors, _warnings = self.Document.with_company(
            self.company
        )._edi_import_files([("a.xml", nfse_xml())])
        self.assertFalse(errors)
        line = documents.fiscal_line_ids
        line.product_id = self.env["product.product"].create(
            {"name": "Reviewed", "type": "service"}
        )
        line.action_resolve_line()
        documents.action_document_confirm()
        original = documents.original_xml_file_id.raw
        mails = self.env["mail.mail"].search_count([])
        self.assertFalse(documents.file_report_id)
        with patch(
            "odoo.addons.mail.models.mail_template.MailTemplate.send_mail"
        ) as send:
            action = documents.view_pdf()
        self.assertFalse(send.called)
        self.assertEqual(action["type"], "ir.actions.act_url")
        self.assertTrue(documents.file_report_id.raw.startswith(b"%PDF"))
        self.assertEqual(documents.original_xml_file_id.raw, original)
        self.assertEqual(self.env["mail.mail"].search_count([]), mails)

    def _migration(self):
        path = os.path.join(
            get_module_path("l10n_br_nfse_dfe"),
            "migrations",
            "16.0.1.1.1",
            "pre-migration.py",
        )
        spec = importlib.util.spec_from_file_location("nfse_dfe_pre_migration", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module.migrate

    def _xmlid_modules(self):
        self.env.cr.execute(
            "SELECT module, res_id FROM ir_model_data "
            "WHERE model = 'ir.model.fields' AND name = %s ORDER BY module",
            (XMLID_NAME,),
        )
        return self.env.cr.fetchall()

    def _own_xmlid(self, module):
        """Give the field the xmlid that ``module`` would have created."""
        field = self.env["ir.model.fields"]._get(
            "res.company", "nfse_import_product_id"
        )
        self.env.cr.execute(
            "DELETE FROM ir_model_data WHERE model = 'ir.model.fields' AND name = %s",
            (XMLID_NAME,),
        )
        for owner in module:
            self.env.cr.execute(
                "INSERT INTO ir_model_data (module, name, model, res_id, noupdate) "
                "VALUES (%s, %s, 'ir.model.fields', %s, false)",
                (owner, XMLID_NAME, field.id),
            )
        return field.id

    def test_the_xmlid_of_the_field_goes_to_l10n_br_nfse(self):
        field_id = self._own_xmlid(["l10n_br_nfse_dfe"])
        self._migration()(self.env.cr, "16.0.1.1.0")
        self.assertEqual(self._xmlid_modules(), [("l10n_br_nfse", field_id)])

    def test_the_xmlid_of_the_dfe_is_dropped_when_the_nfse_has_its_own(self):
        field_id = self._own_xmlid(["l10n_br_nfse", "l10n_br_nfse_dfe"])
        self._migration()(self.env.cr, "16.0.1.1.0")
        self.assertEqual(self._xmlid_modules(), [("l10n_br_nfse", field_id)])

    def test_the_migration_runs_twice_with_the_same_result(self):
        for owners in (["l10n_br_nfse_dfe"], ["l10n_br_nfse", "l10n_br_nfse_dfe"]):
            field_id = self._own_xmlid(owners)
            migrate = self._migration()
            migrate(self.env.cr, "16.0.1.1.0")
            migrate(self.env.cr, "16.0.1.1.0")
            self.assertEqual(self._xmlid_modules(), [("l10n_br_nfse", field_id)])
