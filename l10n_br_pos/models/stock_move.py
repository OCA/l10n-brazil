# -*- coding: utf-8 -*-
# © 2016 KMEE INFORMATICA LTDA (https://kmee.com.br)
#   Luiz Felipe do Divino <luiz.divino@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, fields, api


class StockMove(models.Model):
    _inherit = 'stock.move'

    @api.model
    def _get_price_unit_invoice(self, move, type):
        res = super(StockMove, self)._get_price_unit_invoice(move, type)
        if move.env.context.get('pos_order_id'):
            pos_order_id = move.env.context['pos_order_id']
            pos_order = self.env['pos.order'].browse(pos_order_id)
            for line in pos_order.lines:
                if line.product_id.id == move.product_id.id:
                    return line.price_unit
        return res
