# -*- coding: utf-8 -*-
# (C) 2016 Luis Felipe Mileo - KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import api, models


class StockMove(models.Model):
    _inherit = 'stock.move'

    @api.multi
    def action_confirm(self):
        """
            Pass the fiscal_category_id and the fiscal_position_id
            to the picking
        """
        procs_to_check = self.env['procurement.order']
        for move in self:
            proc = move.procurement_id
            if (proc and proc.sale_line_id and
                    proc.sale_line_id.order_id.fiscal_category_id or
                    proc.sale_line_id.order_id.fiscal_position_id):
                procs_to_check += proc
        res = super(StockMove, self).action_confirm()
        for procurement in procs_to_check:
            for picking in [x.picking_id for x in
                            procurement.move_ids if x.picking_id and not
                            (x.picking_id.fiscal_category_id or
                             x.picking_id.fiscal_position_id)]:
                order = procurement.sale_line_id.order_id
                picking.write({
                    'fiscal_category_id': order.fiscal_category_id and
                    order.fiscal_category_id.id,
                    'fiscal_position_id': order.fiscal_position_id and
                    order.fiscal_position_id.id,
                })
        return res
