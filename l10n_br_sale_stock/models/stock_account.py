# -*- coding: utf-8 -*-
# Copyright (C) 2017  Magno Costa - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import models, api


class StockMove(models.Model):
    _inherit = "stock.move"

    @api.model
    def _get_invoice_line_vals(self, move, partner, inv_type):
        result = super(StockMove, self)._get_invoice_line_vals(
            move, partner, inv_type)
        if move.procurement_id and move.procurement_id.sale_line_id:
            result['partner_order'] = \
                move.procurement_id.sale_line_id.customer_order
            result['partner_order_line'] = \
                move.procurement_id.sale_line_id.customer_order_line

        return result
