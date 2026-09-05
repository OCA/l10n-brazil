# Copyright 2026 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
from io import BytesIO

from brazilfiscalreport.danfse import Danfse, DanfseConfig

from odoo import _, api, models
from odoo.exceptions import UserError

from odoo.addons.l10n_br_fiscal.constants.fiscal import SITUACAO_EDOC_CANCELADA

from ..constants.nfse_nacional import DANFSE_NACIONAL_TEMPLATE


class IrActionsReport(models.Model):
    _inherit = "ir.actions.report"

    def _render_qweb_html(self, report_ref, res_ids, data=None):
        if report_ref == DANFSE_NACIONAL_TEMPLATE:
            return
        return super()._render_qweb_html(report_ref, res_ids, data=data)

    def _render_qweb_pdf(self, report_ref, res_ids, data=None):
        if report_ref != DANFSE_NACIONAL_TEMPLATE:
            return super()._render_qweb_pdf(report_ref, res_ids, data=data)
        documents = self.env["l10n_br_fiscal.document"].browse(res_ids)
        return self._render_danfse_nacional(documents)

    def _render_danfse_nacional(self, documents):
        documents.ensure_one()
        nfse_xml = self._danfse_nacional_xml(documents)
        config = self._get_danfse_nacional_config(documents)
        output = BytesIO()
        Danfse(xml=nfse_xml, config=config).output(output)
        danfse_file = output.getvalue()
        output.close()
        return danfse_file, "pdf"

    @api.model
    def _danfse_nacional_xml(self, document):
        attachment = document.authorization_file_id
        if not attachment:
            raise UserError(
                _(
                    "The DANFSe is rendered from the NFS-e authorized by the ADN, "
                    "and document %s has no authorization XML yet."
                )
                % (document.document_number or document.id)
            )
        return base64.b64decode(attachment.datas)

    @api.model
    def _get_danfse_nacional_config(self, document):
        return DanfseConfig(
            watermark_cancelled=document.state_edoc == SITUACAO_EDOC_CANCELADA,
        )
