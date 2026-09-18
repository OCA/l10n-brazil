# Copyright 2024 Engenere.one
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import base64
from io import BytesIO

from brazilfiscalreport.danfe import Danfe

from odoo import _, api, models
from odoo.exceptions import UserError

from odoo.addons.l10n_br_fiscal.constants.fiscal import SITUACAO_EDOC_CANCELADA


class IrActionsReport(models.Model):
    _inherit = "ir.actions.report"

    def _render_qweb_html(self, report_ref, res_ids, data=None):
        if report_ref == "main_template_danfe":
            return

        return super()._render_qweb_html(report_ref, res_ids, data=data)

    def _render_qweb_pdf(self, report_ref, res_ids, data=None):
        if report_ref not in ["main_template_danfe"]:
            return super()._render_qweb_pdf(report_ref, res_ids, data=data)

        nfe = self.env["l10n_br_fiscal.document"].search([("id", "in", res_ids)])
        return self._render_danfe(nfe)

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
