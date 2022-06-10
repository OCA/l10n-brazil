# Copyright 2019-2020 Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).

from odoo import fields, models


class NfeSpecMixin(models.AbstractModel):
    _description = "Abstract Model"
    _name = "spec.mixin.nfe"
    _field_prefix = "nfe40_"
    _schema_name = "nfe"
    _schema_version = "4.0.0"
    _odoo_module = "l10n_br_nfe"
    _spec_module = "odoo.addons.l10n_br_nfe_spec.models.v4_00.leiauteNFe"
    _binding_module = "nfelib.v4_00.retEnviNFe"
    _spec_tab_name = "NFe"

    brl_currency_id = fields.Many2one(
        comodel_name="res.currency",
        string="Moeda",
        compute="_compute_brl_currency_id",
        store=True,  # TODO FIXME HACK to get v14 to work, should not be like this!!
    )

    def _compute_brl_currency_id(self):
        for item in self:
            item.brl_currency_id = self.env.ref("base.BRL")

    def _valid_field_parameter(self, field, name):
        if name in ("xsd_type", "xsd_required", "choice"):
            return True
        else:
            return super()._valid_field_parameter(field, name)
