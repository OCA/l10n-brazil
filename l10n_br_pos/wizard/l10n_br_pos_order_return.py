# -*- coding: utf-8 -*-
# © 2016 KMEE INFORMATICA LTDA (https://kmee.com.br)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, fields, api


class StockPickingReturn(models.TransientModel):
    _inherit = 'stock.return.picking'

    @api.model
    def default_get(self, fields_list):
        res = super(StockPickingReturn, self).default_get(fields_list)
        if self._context.get('active_model', False) == 'pos.order':
            res.update({'invoice_state': '2binvoiced'})
        return res

class PorOrderReturn(models.TransientModel):

    _name = 'pos.order.return'
    _description = "Pos Order Return"

    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string=u"Cliente",
        help=u"Selecione ou Defina um novo cliente para efetuar a devoluçao",
        required=True
    )

    @staticmethod
    def _check_picking_parameters(order):
        if not order.picking_id.fiscal_category_id:
            order.picking_id.fiscal_category_id = (
                order.session_id.config_id.out_pos_fiscal_category_id or
                order.company_id.out_pos_fiscal_category_id)
        if not order.picking_id.fiscal_category_id.refund_fiscal_category_id:
            order.picking_id.fiscal_category_id.refund_fiscal_category_id = (
                order.session_id.config_id.refund_pos_fiscal_category_id or
                order.company_id.refund_pos_fiscal_category_id)
        order.picking_id.partner_id = order.partner_id
        return True

    @staticmethod
    def _open_return_view(form, ctx):
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'stock.return.picking',
            'views': [(form.id, 'form')],
            'target': 'new',
            'context': ctx,
        }

    @api.multi
    def create_returns(self):
        self.ensure_one()
        active_ids = self._context['active_ids']
        order = self.env['pos.order'].browse(active_ids)
        order.partner_id = self.partner_id

        self._check_picking_parameters(order)

        ctx = dict(self._context)
        ctx['active_ids'] = order.picking_id.ids
        ctx['active_id'] = order.picking_id.id
        ctx['contact_display'] = 'partner_address'
        ctx['search_disable_custom_filters'] = True

        form = self.env.ref('stock.view_stock_return_picking_form', False)

        return self._open_return_view(form, ctx)
