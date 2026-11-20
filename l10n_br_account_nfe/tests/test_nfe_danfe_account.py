# Copyright 2024 Engenere.one
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import base64
from io import BytesIO
from unittest.mock import patch

from reportlab.pdfgen import canvas

from odoo.tests import Form, tagged
from odoo.tools.pdf import PdfFileReader

from odoo.addons.l10n_br_account.tests.common import AccountMoveBRCommon

RENDER_DANFE = (
    "odoo.addons.l10n_br_nfe.report.ir_actions_report"
    ".IrActionsReport.render_danfe_brazilfiscalreport"
)


@tagged("post_install", "-at_install")
class TestDanfe(AccountMoveBRCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.configure_normal_company_taxes()
        cls.env.flush_all()

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

    def _create_nfe(self):
        move_form = Form(
            self.env["account.move"].with_context(default_move_type="out_invoice")
        )
        move_form.partner_id = self.partner_a
        move_form.invoice_date = "2019-01-01"
        move_form.document_type_id = self.env.ref("l10n_br_fiscal.document_55")
        move_form.document_serie_id = self.empresa_lc_document_55_serie_1
        move_form.fiscal_operation_id = self.env.ref("l10n_br_fiscal.fo_venda")
        with move_form.invoice_line_ids.new() as line_form:
            line_form.product_id = self.product_a
            line_form.price_unit = 1000.0
            line_form.fiscal_operation_line_id = self.env.ref(
                "l10n_br_fiscal.fo_venda_venda"
            )
        nfe = move_form.save()
        nfe.action_post()
        return nfe

    def test_generate_danfe_multiple_invoices(self):
        """Printing several invoices at once gives one PDF, in the selection order."""
        first = self._create_nfe()
        second = self._create_nfe()
        for move in first | second:
            move.send_file_id = self.env["ir.attachment"].create(
                {"name": "nfe.xml", "datas": base64.b64encode(b"<nfe/>")}
            )

        def render(nfe, nfe_xml):
            pdf = BytesIO()
            page = canvas.Canvas(pdf)
            page.drawString(100, 750, nfe.document_key or str(nfe.id))
            page.save()
            return pdf.getvalue(), "pdf"

        danfe_report = self.env.ref("l10n_br_account_nfe.report_danfe_account")
        with patch(RENDER_DANFE, side_effect=render) as render_danfe:
            pdf, extension = danfe_report._render_qweb_pdf(
                "main_template_danfe_account", [second.id, first.id]
            )
        self.assertEqual(extension, "pdf")
        self.assertEqual(len(PdfFileReader(BytesIO(pdf)).pages), 2)
        printed = [call.args[0] for call in render_danfe.call_args_list]
        self.assertEqual(printed, [second, first])
