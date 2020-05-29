# Copyright (C) 2013  Raphaël Valyi - Akretion
# Copyright (C) 2014  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.multi
    def _prepare_procurement_values(self, group_id=False):
        values = super()._prepare_procurement_values(group_id)
        # TODO copy fiscal operation
        return values
