# Copyright 2024 Engenere.one
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestDanfe(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))

    def test_generate_danfe_brazil_fiscal_report(self):
        nfe = self.env.ref("l10n_br_account_nfe.demo_nfe_dados_de_cobranca")
        nfe.action_post()

        danfe_report = self.env["ir.actions.report"].search(
            [("report_name", "=", "main_template_danfe_account")]
        )
        danfe_pdf = danfe_report._render_qweb_pdf(
            "main_template_danfe_account", [nfe.id]
        )
        self.assertTrue(danfe_pdf)
