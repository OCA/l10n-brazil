# Copyright (C) 2014  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models


class StockPicking(models.Model):
    _name = 'stock.picking'
    _inherit = [_name, 'l10n_br_fiscal.document.mixin']

    @api.model
    def _default_operation(self):
        fiscal_operation = self.env['l10n_br_fiscal.operation']
        picking_type_id = self.env.context.get('default_picking_type_id')
        if picking_type_id:
            picking_type = self.env['stock.picking.type'].browse(
                picking_type_id)
            fiscal_operation = picking_type.fiscal_operation_id
        return fiscal_operation

    @api.model
    def _operation_domain(self):
        # TODO Check in context to define in or out move default.
        domain = [('state', '=', 'approved')]
        return domain

    operation_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.operation',
        readonly=True,
        states={'draft': [('readonly', False)]},
        default=_default_operation,
        domain=lambda self: self._operation_domain(),
    )
