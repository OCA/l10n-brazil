from odoo import models, fields


class NfeSpecMixin(models.AbstractModel):
    _description = "Abstract Model"
    _inherit = 'spec.mixin'
    _name = 'spec.mixin.nfe'
    # TODO exact schema version
    # TODO tab name...

    brl_currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Moeda',
        compute='_compute_brl_currency_id',
        default=lambda self: self.env.ref('base.BRL').id,
    )

    def _compute_brl_currency_id(self):
        for item in self:
            item.currency_id = self.env.ref('base.BRL').id
