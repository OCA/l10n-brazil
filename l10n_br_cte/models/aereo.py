# Copyright 2023 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


from odoo import fields

from odoo.addons.spec_driven_model.models import spec_models


class Aereo(spec_models.StackedModel):
    _name = "l10n_br_cte.modal.aereo"
    _inherit = "cte.40.aereo"
    _description = "Modal Aereo CTe"

    _cte40_stacking_mixin = "cte.40.aereo"
    _cte40_odoo_module = (
        "odoo.addons.l10n_br_cte_spec.models.v4_0.cte_modal_aereo_v4_00"
    )
    _cte40_binding_module = "nfelib.cte.bindings.v4_0.cte_modal_aereo_v4_00"

    document_id = fields.Many2one(comodel_name="l10n_br_fiscal.document")

    cte40_nMinu = fields.Char(related="document_id.cte40_nMinu")

    cte40_nOCA = fields.Char(related="document_id.cte40_nOCA")

    cte40_dPrevAereo = fields.Date(related="document_id.cte40_dPrevAereo")

    cte40_CL = fields.Char(related="document_id.cte40_CL")

    cte40_cTar = fields.Char(related="document_id.cte40_cTar")

    cte40_vTar = fields.Monetary(related="document_id.cte40_aereo_vTar")

    cte40_xDime = fields.Char(related="document_id.cte40_xDime")

    cte40_peri = fields.One2many(related="document_id.cte40_peri")

    def _prepare_dacte_values(self):
        if not self:
            return {}


class Peri(spec_models.StackedModel):
    _name = "l10n_br_cte.modal.aereo.peri"
    _inherit = "cte.40.peri"
    _description = """Preenchido quando for transporte de produtos classificados pela
    ONU como perigosos. O preenchimento desses campos não desobriga a empresa aérea de
    emitir os demais documentos que constam na legislação vigente."""

    _cte40_stacking_mixin = "cte.40.peri"
    _cte40_odoo_module = (
        "odoo.addons.l10n_br_cte_spec.models.v4_0.cte_modal_aereo_v4_00"
    )
    _cte40_binding_module = "nfelib.cte.bindings.v4_0.cte_modal_aereo_v4_00"

    document_id = fields.Many2one(comodel_name="l10n_br_fiscal.document")

    cte40_nONU = fields.Char(required=True)

    cte40_qTotEmb = fields.Char(required=True)

    cte40_qTotProd = fields.Float(required=True)

    cte40_uniAP = fields.Selection(required=True)
