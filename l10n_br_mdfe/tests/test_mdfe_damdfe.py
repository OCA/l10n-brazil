# Copyright 2024 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase

from .test_mdfe_serialize import TestMDFeSerialize


class TestDamdfeGeneration(TransactionCase):
    def test_generate_damdfe_brazil_fiscal_report(self):
        mdfe = self.env.ref("l10n_br_mdfe.demo_mdfe_lc_modal_rodoviario")
        TestMDFeSerialize.prepare_modal_rodoviario_data(mdfe)
        mdfe.action_document_confirm()
        mdfe.view_pdf()
        self.assertTrue(mdfe.file_report_id)

    def test_generate_damdfe_document_type_error(self):
        damdfe_report = self.env["ir.actions.report"].search(
            [("report_name", "=", "main_template_damdfe")]
        )
        mdfe = self.env.ref("l10n_br_mdfe.demo_mdfe_lc_modal_rodoviario")
        mdfe.document_type_id = self.env.ref("l10n_br_fiscal.document_01")
        TestMDFeSerialize.prepare_modal_rodoviario_data(mdfe)
        mdfe.action_document_confirm()
        with self.assertRaises(UserError) as captured_exception:
            damdfe_report._render_qweb_pdf("main_template_damdfe", [mdfe.id])
        self.assertEqual(
            captured_exception.exception.args[0],
            "You can only print a DAMDFE of a MDFe(58).",
        )

    def test_generate_damdfe_brazil_fiscal_report_partner(self):
        mdfe = self.env.ref("l10n_br_mdfe.demo_mdfe_lc_modal_rodoviario")
        TestMDFeSerialize.prepare_modal_rodoviario_data(mdfe)
        mdfe.action_document_confirm()
        mdfe.with_context(skip_edoc_lock=True).issuer = "partner"
        mdfe.view_pdf()
        self.assertTrue(mdfe.file_report_id)
