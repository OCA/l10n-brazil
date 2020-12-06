from odoo import models, fields


class NfeSpecMixin(models.AbstractModel):
    _description = "Abstract Model"
    _name = 'spec.mixin.nfe'
    _field_prefix = 'nfe40_'
    _schema_name = 'nfe'
    _schema_version = '4.0.0'
    _odoo_module = 'l10n_br_nfe'
    _spec_module = 'odoo.addons.l10n_br_nfe_spec.models.v4_00.leiauteNFe'
    _spec_tab_name = 'NFe'

    brl_currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Moeda',
        compute='_compute_brl_currency_id',
        default=lambda self: self.env.ref('base.BRL').id,
    )

    def _compute_brl_currency_id(self):
        for item in self:
            item.currency_id = self.env.ref('base.BRL').id
