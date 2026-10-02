# Copyright 2024 Engenere.one
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import base64
from io import BytesIO

from brazilfiscalreport.dacce import DaCCe
from brazilfiscalreport.danfe import Danfe

from odoo import _, api, models
from odoo.exceptions import UserError
from odoo.tools.pdf import merge_pdf

from odoo.addons.l10n_br_fiscal.constants.fiscal import SITUACAO_EDOC_CANCELADA

DOCUMENT_EVENT_REPORT = "l10n_br_fiscal_edi.main_report_document_event"
HOMOLOGATION_MARK = "SEM VALOR FISCAL"


class IrActionsReport(models.Model):
    _inherit = "ir.actions.report"

    def _render_qweb_html(self, report_ref, res_ids, data=None):
        if report_ref == "main_template_danfe":
            return

        return super()._render_qweb_html(report_ref, res_ids, data=data)

    def _render_qweb_pdf(self, report_ref, res_ids, data=None):
        if report_ref not in ["main_template_danfe"]:
            if self._is_document_event_report(report_ref):
                return self._render_document_event(report_ref, res_ids, data=data)
            return super()._render_qweb_pdf(report_ref, res_ids, data=data)

        nfe = self.env["l10n_br_fiscal.document"].search([("id", "in", res_ids)])
        return self._render_danfe(nfe)

    @api.model
    def _is_document_event_report(self, report_ref):
        report = self._get_report(report_ref)
        return bool(report) and report.report_name == DOCUMENT_EVENT_REPORT

    def _render_document_event(self, report_ref, res_ids, data=None):
        """Print the events: the DACCE for the correction letters that have a
        procEventoNFe, the QWeb report for any other.
        """
        events = self.env["l10n_br_fiscal.event"].browse(res_ids)
        rendered = []
        for event in events:
            event._check_can_print()
            if event._get_proc_evento_nfe():
                rendered.append((self.render_dacce_brazilfiscalreport(event), "pdf"))
            else:
                rendered.append(
                    super()._render_qweb_pdf(report_ref, event.ids, data=data)
                )
        if len(rendered) == 1:
            return rendered[0]
        return merge_pdf([content for content, _fmt in rendered]), "pdf"

    def render_dacce_brazilfiscalreport(self, event):
        proc_xml = event._get_proc_evento_nfe()
        company = event.company_id
        logo = False
        if company.logo:
            logo = BytesIO(base64.b64decode(company.logo))
        dacce = DaCCe(xml=proc_xml, emitente=event._get_dacce_issuer(), image=logo)
        if event._is_homologation():
            self._draw_homologation_mark(dacce)
        output = BytesIO()
        dacce.output(output)
        return output.getvalue()

    @api.model
    def _draw_homologation_mark(self, pdf):
        """The library does not mark the documents of the test environment."""
        with pdf.local_context(fill_opacity=0.25):
            pdf.set_font("Helvetica", "B", 48)
            pdf.set_text_color(160, 160, 160)
            with pdf.rotation(angle=45, x=105, y=170):
                pdf.text(x=28, y=170, text=HOMOLOGATION_MARK)
            pdf.set_text_color(0, 0, 0)

    def _render_danfe(self, nfe):
        if nfe.document_type != "55":
            raise UserError(_("You can only print a DANFE of a NFe(55)."))

        nfe_xml = False
        if nfe.authorization_file_id:
            nfe_xml = base64.b64decode(nfe.authorization_file_id.datas)
        elif nfe.send_file_id:
            nfe_xml = base64.b64decode(nfe.send_file_id.datas)

        if not nfe_xml:
            raise UserError(_("No xml file was found."))

        return self.render_danfe_brazilfiscalreport(nfe, nfe_xml)

    def render_danfe_brazilfiscalreport(self, nfe, nfe_xml):
        logo = False
        if nfe.issuer == "company" and nfe.company_id.logo:
            logo = base64.b64decode(nfe.company_id.logo)
        elif nfe.issuer != "company" and nfe.company_id.logo_web:
            logo = base64.b64decode(nfe.company_id.logo_web)

        if logo:
            tmpLogo = BytesIO()
            tmpLogo.write(logo)
            tmpLogo.seek(0)
        else:
            tmpLogo = False
        config = self._get_danfe_config(tmpLogo, nfe.company_id)
        # The cancellation is not in the authorization XML: only the document
        # knows about it.
        config.watermark_cancelled = nfe.state_edoc == SITUACAO_EDOC_CANCELADA

        danfe = Danfe(xml=nfe_xml, config=config)

        tmpDanfe = BytesIO()
        danfe.output(tmpDanfe)
        danfe_file = tmpDanfe.getvalue()
        tmpDanfe.close()

        return danfe_file, "pdf"

    @api.model
    def _get_danfe_config(self, tmpLogo, company):
        return company.danfe_profile_id._get_danfe_config(logo=tmpLogo)
