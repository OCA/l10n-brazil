# Copyright 2026-TODAY Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).

from odoo import fields, models


class NfseSpecMixin(models.AbstractModel):
    _description = "Abstract Model"
    _name = "spec.mixin.nfse"
    _nfse10_odoo_module = (
        "odoo.addons.l10n_br_nfse_spec.models.v1_0.tipos_complexos_v1_00"
    )
    _nfse10_binding_module = "nfelib.nfse.bindings.v1_0.tipos_complexos_v1_00"

    brl_currency_id = fields.Many2one(
        comodel_name="res.currency",
        string="Moeda",
        compute="_compute_brl_currency_id",
        default=lambda self: self.env.ref("base.BRL"),
    )

    def _compute_brl_currency_id(self):
        # batch assignment: same value for every record, avoids a Python
        # loop and a per-record cache write
        self.brl_currency_id = self.env.ref("base.BRL")

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
