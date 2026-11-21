# Copyright 2026 KMEE - Luis Felipe Mileo <mileo@kmee.com.br>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).

from odoo import fields, models


class GnreSpecMixin(models.AbstractModel):
    _description = "Abstract Model"
    _name = "spec.mixin.gnre"
    _gnre20_odoo_module = "odoo.addons.l10n_br_gnre_spec.models.v2_0.lote_gnre_v2_00"
    _gnre20_binding_module = "nfelib.gnre.bindings.v2_0.lote_gnre_v2_00"

    brl_currency_id = fields.Many2one(
        comodel_name="res.currency",
        string="Moeda",
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
