# Copyright (C) 2009  Renato Lima - Akretion, Gabriel C. Stabel
# Copyright (C) 2012  Raphaël Valyi - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from datetime import datetime

from odoo import api, fields, models
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    @api.multi
    def _prepare_stock_moves(self, picking):
        """
        Prepare the stock moves data for one order line.
         This function returns a list of
        dictionary ready to be used in stock.move's create()
        """
        self.ensure_one()
        vals = super(PurchaseOrderLine, self)._prepare_stock_moves(picking)
        vals[0].update({
            'fiscal_category_id': self.fiscal_category_id.id,
            'fiscal_position_id': self.fiscal_position_id.id,
        })
        return vals
