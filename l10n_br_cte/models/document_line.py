# Copyright 2023 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields

from odoo.addons.spec_driven_model.models import spec_models


class CTeLine(spec_models.StackedModel):
    _name = "l10n_br_fiscal.document.line"
    _inherit = ["l10n_br_fiscal.document.line", "cte.40.tcte_vprest_comp"]
    _stacked = "cte.40.tcte_vprest_comp"
    _field_prefix = "cte40_"
    _schema_name = "cte"
    _schema_version = "4.0.0"
    _odoo_module = "l10n_br_cte"
    _spec_module = "odoo.addons.l10n_br_cte_spec.models.v4_0.cte_tipos_basico_v4_00"
    _spec_tab_name = "CTe"
    _stacking_points = {}
    _stack_skip = ("cte40_Comp_vPrest_id",)
    _binding_module = "nfelib.cte.bindings.v4_0.cte_tipos_basico_v4_00"

    ##########################
    # CT-e tag: comp
    ##########################

    cte40_xNome = fields.Text(related="name")

    cte40_vComp = fields.Monetary(related="amount_total")
