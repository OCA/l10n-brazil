# Copyright 2025 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models

from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    MODELO_FISCAL_NFCE,
    MODELO_FISCAL_NFE,
)


class L10n_br_fiscalDocumentLineImportWizard(models.TransientModel):
    _inherit = "l10n_br_fiscal.document.line.import.wizard"

    def _prepare_onchange_document_line_id(self):
        res = super()._prepare_onchange_document_line_id()
        if self.document_line_id.document_id.document_type in [
            MODELO_FISCAL_NFE,
            MODELO_FISCAL_NFCE,
        ]:
            if self.document_line_id.line_import_json:
                line_json = self.document_line_id.line_import_json
                vals = {
                    "document_code": line_json.get("nfe40_cProd"),
                    "document_ean": line_json.get("nfe40_cEAN"),
                    "document_name": line_json.get("nfe40_xProd"),
                    "document_qty": line_json.get("nfe40_qCom"),
                    "document_uom": line_json.get("nfe40_uCom"),
                    "document_uom_trib": line_json.get("nfe40_uTrib"),
                    # "document_ncm_id": document_line.ncm_id.id,
                    # "document_cfop_id": document_line.cfop_id.id,
                }
                self.update(vals)
        return res
