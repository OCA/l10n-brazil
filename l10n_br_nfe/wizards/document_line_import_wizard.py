# Copyright 2025 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models

from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    MODELO_FISCAL_NFCE,
    MODELO_FISCAL_NFE,
)


class FiscalDocumentLineImportWizard(models.TransientModel):
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
                    # "document_name": line_json.get("nfe40_NCM"),
                    # "document_name": line_json.get("nfe40_CEST"),
                    # "document_name": line_json.get("nfe40_indEscala"),
                    # "document_name": line_json.get("nfe40_CFOP"),
                    "document_uom": line_json.get("nfe40_uCom"),
                    "document_qty": line_json.get("nfe40_qCom"),
                    # "document_name": line_json.get("nfe40_vUnCom"),
                    # "document_name": line_json.get("nfe40_vProd"),
                    # "document_name": line_json.get("nfe40_cEANTrib"),
                    "document_uom_trib": line_json.get("nfe40_uTrib"),
                    # "document_name": line_json.get("nfe40_qTrib"),
                    # "document_name": line_json.get("nfe40_vUnTrib"),
                    # "document_name": line_json.get("nfe40_indTot"),
                }
                self.update(vals)
        return res

    def _check_other_lines_info(self, values):
        res = super()._check_other_lines_info(values)
        if self.document_line_id.document_id.document_type in [
            MODELO_FISCAL_NFE,
            MODELO_FISCAL_NFCE,
        ]:
            fiscal_line_ids = self.document_line_id.document_id.fiscal_line_ids
            for line in fiscal_line_ids:
                if not line.line_import_json:
                    continue
                line_json = self.document_line_id.line_import_json

                if not line.uom_id and line_json.get("nfe40_uCom") == self.document_uom:
                    line.uom_id = self.import_uom_id

                # if not line.uom_id and line_json.get("nfe40_uTrib")
                #   == self.document_uom_trib:
                #     line.uom_id = self.import_uom_id

                # if not line.ncm_id and line_json.get("nfe40_NCM")
                # == self.import_ncm_id.code:
                #     line.ncm_id = self.import_ncm_id

                # if not line.cfop_id and line_json.get("nfe40_CFOP")
                # == self.import_cfop_id.code:
                #     line.cfop_id = self.import_cfop_id

        return res
