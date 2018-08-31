# -*- coding: utf-8 -*-
# © 2016 KMEE INFORMATICA LTDA (https://kmee.com.br)
#   Luiz Felipe do Divino <luiz.divino@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, fields, api


class StockMove(models.Model):
    _inherit = 'stock.move'

    @api.model
    def _get_price_unit_invoice(self, move_line, type):
        # No link between the pos.order.line and its stock.move
        pos_order_line_product_price_map = dict(move_line.mapped(
            'origin_returned_move_id.picking_id.pos_order_ids.lines'
        ).mapped(
            lambda order_line: (order_line.product_id, order_line.price_unit)
        ))
        return (
            pos_order_line_product_price_map.get(move_line.product_id)
            if move_line.product_id in pos_order_line_product_price_map
            else super(StockMove, self)._get_price_unit_invoice(move_line, type)
        )
