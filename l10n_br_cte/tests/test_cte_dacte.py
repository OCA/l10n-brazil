# Copyright 2024 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


class TestDacteGeneration(TransactionCase):
    def test_generate_dacte_brazil_fiscal_report(self):
        cte = self.env.ref("l10n_br_cte.demo_cte_lc_modal_rodoviario")
        cte.action_document_confirm()
        cte.view_pdf()
        self.assertTrue(cte.file_report_id)

    def test_generate_dacte_document_type_error(self):
        dacte_report = self.env["ir.actions.report"].search(
            [("report_name", "=", "main_template_dacte")]
        )
        cte = self.env.ref("l10n_br_cte.demo_cte_lc_modal_rodoviario")
        cte.document_type_id = self.env.ref("l10n_br_fiscal.document_01")
        cte.action_document_confirm()
        with self.assertRaises(UserError) as captured_exception:
            dacte_report._render_qweb_pdf("main_template_dacte", [cte.id])
        self.assertEqual(
            captured_exception.exception.args[0],
            "You can only print a DACTE of a CTe(57).",
        )

    def test_generate_dacte_brazil_fiscal_report_partner(self):
        cte = self.env.ref("l10n_br_cte.demo_cte_lc_modal_rodoviario")
        cte.action_document_confirm()
        cte.issuer = "partner"
        cte.view_pdf()
        self.assertTrue(cte.file_report_id)
