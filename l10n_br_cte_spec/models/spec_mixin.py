# Copyright 2019-2020 Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).

from odoo import fields, models


class CteSpecMixin(models.AbstractModel):
    _description = "Abstract Model"
    _name = "spec.mixin.cte"
    _field_prefix = "cte40_"
    _cte40_odoo_module = (
        "odoo.addons.l10n_br_cte_spec.models.v4_0.cte_tipos_basico_v4_00"
    )
    _cte40_binding_module = "nfelib.cte.bindings.v4_0.cte_tipos_basico_v4_00"

    #: Additional m2o search keys (and extra domain) per comodel used when
    #: matching existing records during CT-e imports, so per-comodel override
    #: files (res_city.py, res_country.py, res_country_state.py) are not
    #: needed.
    _cte_m2o_search_keys = {
        "res.city": ["ibge_code"],
        "res.country": ["bc_code"],
        "res.country.state": ["ibge_code", "code"],
    }
    _cte_m2o_extra_domain = {"res.country.state": [("ibge_code", "!=", False)]}

    brl_currency_id = fields.Many2one(
        comodel_name="res.currency",
        string="Moeda",
        # FIXME compute method is better, but not working in v14.
        default=lambda self: self.env.ref("base.BRL"),
    )

    def _valid_field_parameter(self, field, name):
        if name in (
            "xsd_type",
            "xsd_required",
            "choice",
            "xsd_implicit",
            "xsd_choice_required",
        ):
            return True
        else:
            return super()._valid_field_parameter(field, name)
