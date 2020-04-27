# Copyright (C) 2014  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models


class StockPicking(models.Model):
    _name = 'stock.picking'
    _inherit = [_name, 'l10n_br_fiscal.document.mixin']

    @api.model
    def _default_operation(self):
        # TODO Check in context to define in or out move default.
        return self.env.user.company_id.stock_fiscal_operation_id

    @api.model
    def _operation_domain(self):
        # TODO Check in context to define in or out move default.
        domain = [('state', '=', 'approved')]
        return domain

    operation_id = fields.Many2one(
        readonly=True,
        states={'draft': [('readonly', False)]},
        default=_default_operation,
        domain=lambda self: self._operation_domain(),
    )
