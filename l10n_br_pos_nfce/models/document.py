# License AGPL-3 - See [http://www.gnu.org/licenses/agpl-3.0.html](http://www.gnu.org/licenses/agpl-3.0.html)

from odoo import models

from odoo.addons.l10n_br_fiscal.constants.fiscal import MODELO_FISCAL_NFCE
from odoo.addons.l10n_br_nfe.models.document import filter_processador_edoc_nfe


class Document(models.Model):
    _inherit = "l10n_br_fiscal.document"

    def _serialize(self, edocs):
        for record in self.with_context(lang="pt_BR").filtered(
            filter_processador_edoc_nfe
        ):
            if record.document_type == MODELO_FISCAL_NFCE:
                record._document_qrcode()

        edocs = super()._serialize(edocs)

        for record in self.with_context(lang="pt_BR").filtered(
            filter_processador_edoc_nfe
        ):
            processor = record.processador_edoc

            record.flush_recordset()
            record.invalidate_recordset()

            if hasattr(record, "move_ids") and record.move_ids:
                record.move_ids.processador_edoc = processor

            record.processador_edoc = processor

        return edocs

    def _prepare_nfce_send(self):
        self.ensure_one()
        res = super()._prepare_nfce_send()

        self.nfe40_detPag.filtered(lambda p: p.nfe40_tPag == "99").write(
            {"nfe40_xPag": "Outros"}
        )
        return res

    def _document_qrcode(self):
        res = super()._document_qrcode()

        for record in self.filtered(lambda d: d.document_type == MODELO_FISCAL_NFCE):
            if record.nfe40_infNFeSupl:
                record.nfe40_infNFeSupl.unlink()

            record.nfe40_infNFeSupl = self.env[
                "l10n_br_fiscal.document.supplement"
            ].create(
                {
                    "qrcode": record.get_nfce_qrcode(),
                    "url_key": record.get_nfce_qrcode_url(),
                }
            )

        return res
