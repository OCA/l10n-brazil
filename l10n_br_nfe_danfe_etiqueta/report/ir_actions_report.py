# Copyright 2026 PopSolutions
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import base64
from io import BytesIO

from brazilfiscalreport.danfe import DanfeEtiqueta

from odoo import _, api, models
from odoo.exceptions import UserError

from odoo.addons.l10n_br_fiscal.constants.fiscal import SITUACAO_EDOC_CANCELADA

ETIQUETA_REPORT = "main_template_danfe_etiqueta"


class IrActionsReport(models.Model):
    _inherit = "ir.actions.report"

    def _render_qweb_html(self, report_ref, res_ids, data=None):
        if report_ref == ETIQUETA_REPORT:
            return

        return super()._render_qweb_html(report_ref, res_ids, data=data)

    def _render_qweb_pdf(self, report_ref, res_ids, data=None):
        if report_ref != ETIQUETA_REPORT:
            return super()._render_qweb_pdf(report_ref, res_ids, data=data)

        nfe = self.env["l10n_br_fiscal.document"].search([("id", "in", res_ids)])
        return self._render_danfe_etiqueta(nfe)

    def _render_danfe_etiqueta(self, nfe):
        if nfe.document_type != "55":
            raise UserError(
                _("You can only print a DANFE Simplificado - Etiqueta of a NFe(55).")
            )

        nfe_xml = False
        if nfe.authorization_file_id:
            nfe_xml = base64.b64decode(nfe.authorization_file_id.datas)
        elif nfe.send_file_id:
            nfe_xml = base64.b64decode(nfe.send_file_id.datas)

        if not nfe_xml:
            raise UserError(_("No xml file was found."))

        config = self._get_danfe_etiqueta_config(nfe.company_id)
        # The cancellation is not in the authorization XML: only the document
        # knows about it.
        config.watermark_cancelled = nfe.state_edoc == SITUACAO_EDOC_CANCELADA

        etiqueta = DanfeEtiqueta(xml=nfe_xml, config=config)

        tmp_etiqueta = BytesIO()
        etiqueta.output(tmp_etiqueta)
        etiqueta_file = tmp_etiqueta.getvalue()
        tmp_etiqueta.close()

        return etiqueta_file, "pdf"

    @api.model
    def _get_danfe_etiqueta_config(self, company):
        return company.danfe_profile_id._get_danfe_etiqueta_config()
