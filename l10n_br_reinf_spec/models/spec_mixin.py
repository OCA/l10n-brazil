# Copyright 2026 Akretion - Raphaël Valyi <raphael.valyi@akretion.com>
# Copyright 2026 KMEE - Luis Felipe Mileo <mileo@kmee.com.br>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).

from odoo import fields, models


class ReinfSpecMixin(models.AbstractModel):
    _description = "Abstract Model"
    _name = "spec.mixin.reinf"
    _field_prefix = "reinf21_"

    # The EFD-Reinf has one XSD and one generated module per event, so the pair
    # below is only a fallback: every concrete model of l10n_br_reinf must
    # redeclare it with the module of the event it maps.
    _reinf21_odoo_module = (
        "odoo.addons.l10n_br_reinf_spec.models.v2_01_02"
        ".r_4020_evt4020_pagto_beneficiario_pj_v2_01_02"
    )
    _reinf21_binding_module = (
        "nfelib.reinf.bindings.v2_01_02.r_4020_evt4020_pagto_beneficiario_pj_v2_01_02"
    )

    brl_currency_id = fields.Many2one(
        comodel_name="res.currency",
        string="Currency",
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
