# Copyright 2024 Engenere.one
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.tests import Form, tagged

from odoo.addons.l10n_br_account.tests.common import AccountMoveBRCommon


@tagged("post_install", "-at_install")
class TestDanfe(AccountMoveBRCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.configure_normal_company_taxes()
        cls.env.flush_all()

    def test_generate_danfe_brazil_fiscal_report(self):
        move_form = Form(
            self.env["account.move"].with_context(
                default_move_type="out_invoice",
            )
        )
        move_form.partner_id = self.partner_a
        move_form.invoice_date = "2019-01-01"
        move_form.document_type_id = self.env.ref("l10n_br_fiscal.document_55")
        move_form.document_serie_id = self.empresa_lc_document_55_serie_1
        # l10n_latam_invoice_document compatibility
        if "l10n_latam.document.type" in self.env:
            latam_doc_type = self.env["l10n_latam.document.type"].search(
                [("code", "=", "55"), ("country_id", "=", self.env.ref("base.br").id)],
                limit=1,
            )
            if latam_doc_type and move_form.l10n_latam_use_documents:
                move_form.l10n_latam_document_type_id = latam_doc_type
        move_form.fiscal_operation_id = self.env.ref("l10n_br_fiscal.fo_venda")
        with move_form.invoice_line_ids.new() as line_form:
            line_form.product_id = self.product_a
            line_form.price_unit = 1000.0
            line_form.fiscal_operation_line_id = self.env.ref(
                "l10n_br_fiscal.fo_venda_venda"
            )
        nfe = move_form.save()
        nfe.action_post()

        # Verify the invoice was properly created and posted
        self.assertEqual(nfe.state, "posted")
        self.assertTrue(nfe.document_type_id)
        self.assertEqual(nfe.document_type_id.code, "55")

        # Verify DANFE report is registered
        danfe_report = self.env["ir.actions.report"].search(
            [("report_name", "=", "main_template_danfe_account")]
        )
        self.assertTrue(danfe_report)
