# Copyright 2021 Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).

from odoo import fields, models


class PoXsdMixin(models.AbstractModel):
    _description = "Abstract Model for PO XSD"
    _name = "spec.mixin.poxsd"
    _field_prefix = "poxsd10_"
    _schema_name = "poxsd"
    _schema_version = "1.0"
    _odoo_module = "poxsd"
    _spec_module = "odoo.addons.spec_driven_model.tests.spec_poxsd"
    _binding_module = "odoo.addons.spec_driven_model.tests.purchase_order_lib"

    # TODO rename
    brl_currency_id = fields.Many2one(
        comodel_name="res.currency",
        string="Moeda",
        compute="_compute_brl_currency_id",
        default=lambda self: self.env.ref("base.EUR").id,
    )

    def _compute_brl_currency_id(self):
        for item in self:
            item.brl_currency_id = self.env.ref("base.EUR").id

    def _valid_field_parameter(self, field, name):
        if name in ("xsd_type", "xsd_required", "choice", "xsd_implicit"):
            return True
        else:
            return super()._valid_field_parameter(field, name)
