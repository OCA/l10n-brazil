# Copyright 2024 Engenere.one
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from unittest.mock import patch

from odoo.tests import SavepointCase, tagged


@tagged("post_install", "-at_install")
class TestDanfe(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def test_generate_danfe_brazil_fiscal_report(self):
        nfe = self.env.ref("l10n_br_account_nfe.demo_nfe_dados_de_cobranca")
        nfe.action_post()

        danfe_report = self.env["ir.actions.report"].search(
            [("report_name", "=", "main_template_danfe_account")]
        )
        danfe_pdf = danfe_report._render_qweb_pdf([nfe.id])
        self.assertTrue(danfe_pdf)

    def test_generate_danfe_erpbrasil_edoc(self):
        nfe = self.env.ref("l10n_br_account_nfe.demo_nfe_dados_de_cobranca")
        nfe.company_id.danfe_library = "erpbrasil.edoc.pdf"

        with patch("erpbrasil.edoc.pdf.base.ImprimirXml.imprimir") as mock_make_pdf:
            mock_make_pdf.return_value = b"Mock PDF"

            nfe.action_post()

            danfe_report = self.env["ir.actions.report"].search(
                [("report_name", "=", "main_template_danfe_account")]
            )
            danfe_pdf = danfe_report._render_qweb_pdf([nfe.id])
            self.assertTrue(danfe_pdf)
