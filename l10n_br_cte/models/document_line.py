# Copyright 2023 KMEE
# Copyright 2024 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields

from odoo.addons.spec_driven_model.models import spec_models


class CTeLine(spec_models.StackedModel):
    _name = "l10n_br_fiscal.document.line"
    _inherit = ["l10n_br_fiscal.document.line", "cte.40.tcte_vprest_comp"]

    _cte40_odoo_module = (
        "odoo.addons.l10n_br_cte_spec.models.v4_0.cte_tipos_basico_v4_00"
    )
    _cte40_stacking_mixin = "cte.40.tcte_vprest_comp"
    _cte40_stacking_skip_paths = ("cte40_Comp_vPrest_id",)

    ##########################
    # CT-e tag: comp
    ##########################

    cte40_xNome = fields.Char(related="name")

    cte40_vComp = fields.Monetary(related="amount_total")

    # FIXME ORM/spec_model_driven workaround
    # see https://github.com/OCA/l10n-brazil/pull/3651#issuecomment-2729890350
    cte40_Comp_vPrest_id = fields.Many2one(copy=False)
