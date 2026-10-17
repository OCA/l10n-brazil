# Copyright 2026 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).

from odoo import fields, models


class DereSpecMixin(models.AbstractModel):
    _name = "spec.mixin.dere"
    _description = "DeRE spec mixin"

    _dere12_odoo_module = "odoo.addons.l10n_br_dere_spec.models.v1_2.evt_info_contrib"

    def _valid_field_parameter(self, field, name):
        if name in (
            "xsd_type",
            "xsd_required",
            "choice",
            "xsd_implicit",
            "xsd_choice_required",
        ):
            return True
        return super()._valid_field_parameter(field, name)


class Dere12CurrencyMixin(models.AbstractModel):
    _name = "spec.mixin.dere.currency"
    _description = "DeRE currency helper"

    brl_currency_id = fields.Many2one(
        comodel_name="res.currency",
        string="Currency",
        default=lambda self: self.env.ref("base.BRL"),
    )
