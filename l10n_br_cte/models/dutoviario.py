# Copyright 2023 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields

from odoo.addons.spec_driven_model.models import spec_models


class Duto(spec_models.StackedModel):
    _name = "l10n_br_cte.modal.duto"
    _inherit = "cte.40.duto"
    _description = "Modal Dutoviario CTe"

    _cte40_stacking_mixin = "cte.40.duto"
    _cte40_odoo_module = (
        "odoo.addons.l10n_br_cte_spec.models.v4_0.cte_modal_dutoviario_v4_00"
    )
    _cte40_binding_module = "nfelib.cte.bindings.v4_0.cte_modal_dutoviario_v4_00"

    document_id = fields.Many2one(comodel_name="l10n_br_fiscal.document")

    cte40_dIni = fields.Date(related="document_id.cte40_dIni")

    cte40_dFim = fields.Date(related="document_id.cte40_dFim")

    cte40_vTar = fields.Float(related="document_id.cte40_vTar")

    def _prepare_dacte_values(self):
        if not self:
            return {}
