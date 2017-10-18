# -*- coding: utf-8 -*-
# © 2016 KMEE INFORMATICA LTDA (https://kmee.com.br)
#   Luiz Felipe do Divino <luiz.divino@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, fields, api


class StockMove(models.Model):
    _inherit = 'stock.move'

    pos_order_line = fields.Many2one(
        string="Pos Order Line",
        comodel_name="pos.order.line"
    )

    @api.model
    def create(self, vals):
        res = super(StockMove, self).create(vals)
        if res.picking_id.pos_order_ids and not res.pos_order_line:
            pos_order_line = self.env['pos.order.line'].search([
                ('order_id', '=', res.picking_id.pos_order_ids.ids),
                ('product_id', '=', vals['product_id'])
            ])
            res.pos_order_line = pos_order_line.id

        return res

    @api.model
    def _get_price_unit_invoice(self, move, type):
        res = super(StockMove, self)._get_price_unit_invoice(move, type)
        if move.pos_order_line:
            return move.pos_order_line.price_unit
        return res
