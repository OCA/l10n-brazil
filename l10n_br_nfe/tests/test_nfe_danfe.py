# Copyright 2024 Engenere.one
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


class TestDanfeGeneration(TransactionCase):
    def test_generate_danfe_brazil_fiscal_report(self):
        nfe = self.env.ref("l10n_br_nfe.demo_nfe_natural_icms_18_red_51_11")
        nfe.action_document_confirm()
        nfe.view_pdf()
        self.assertTrue(nfe.file_report_id)

    def test_generate_danfe_document_type_error(self):
        danfe_report = self.env["ir.actions.report"].search(
            [("report_name", "=", "main_template_danfe")]
        )
        nfe = self.env.ref("l10n_br_nfe.demo_nfe_natural_icms_18_red_51_11")
        nfe.document_type_id = self.env.ref("l10n_br_fiscal.document_01")
        nfe.action_document_confirm()
        with self.assertRaises(UserError) as captured_exception:
            danfe_report._render_qweb_pdf("main_template_danfe", [nfe.id])
        self.assertEqual(
            captured_exception.exception.args[0],
            "You can only print a DANFE of a NFe(55).",
        )

    def test_generate_danfe_brazil_fiscal_report_partner(self):
        nfe = self.env.ref("l10n_br_nfe.demo_nfe_natural_icms_18_red_51_11")
        nfe.action_document_confirm()
        nfe.issuer = "partner"
        nfe.view_pdf()
        self.assertTrue(nfe.file_report_id)
