# -*- coding: utf-8 -*-
# © 2016 KMEE INFORMATICA LTDA (https://kmee.com.br)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, fields, api, _
from openerp.exceptions import Warning


class StockPickingReturn(models.TransientModel):
    _inherit = 'stock.return.picking'

    @api.model
    def default_get(self, fields_list):
        res = super(StockPickingReturn, self).default_get(fields_list)
        if self._context.get('active_model', False) == 'pos.order':
            res.update({'invoice_state': '2binvoiced'})
        return res

    @api.multi
    def _buscar_valor_total_devolucao(self, pos_order):
        precos_produtos_pos_order = {}
        for line in pos_order.lines:
            precos_produtos_pos_order.update({
                line.product_id.id: line.price_unit
            })
        valor_total_devolucao = 0.00
        for line in self.product_return_moves:
            valor_total_devolucao += \
                precos_produtos_pos_order[line.product_id.id] * line.quantity

        return valor_total_devolucao

    @api.multi
    def create_returns(self):
        if self.env.context.get('pos_order_id'):
            pos_order = self.env['pos.order'].browse(
                self.env.context['pos_order_id']
            )
            for product_line in self.product_return_moves:
                for line in pos_order.lines:
                    if line.product_id == product_line.product_id:
                        if line.qtd_produtos_devolvidos + product_line.quantity > line.qty:
                            raise Warning(
                                _('Esta quantidade do produto %s não pode '
                                'ser devolvida') % (line.product_id.display_name))
            res = super(StockPickingReturn, self).create_returns()
            valor_total_devolucao = self._buscar_valor_total_devolucao(
                pos_order
            )
            pos_order.partner_id.credit_limit = valor_total_devolucao
            return res

        return super(StockPickingReturn, self).create_returns()


class PorOrderReturn(models.TransientModel):
    _name = 'pos.order.return'
    _description = "Pos Order Return"

    @api.model
    def _get_partner(self):
        order_id = self._context.get('active_id', False)
        partner = self.env['pos.order'].browse(order_id).partner_id
        if partner:
            return partner

    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string=u"Cliente",
        help=u"Selecione ou Defina um novo cliente para efetuar a devoluçao",
        default=_get_partner,
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
        obj_fp_rule = self.env['account.fiscal.position.rule']
        kwargs = {
            'partner_id': self.partner_id.id,
            'partner_invoice_id':
                self.partner_id.id,
            'partner_shipping_id':
                self.partner_id.id,
            'fiscal_category_id':
                order.picking_id.fiscal_category_id.id,
            'company_id': self.env.user.company_id.id,
        }
        fiscal_position_id = obj_fp_rule.apply_fiscal_mapping(
            {'value': {}}, **kwargs
        )['value']['fiscal_position']
        order.picking_id.fiscal_position = fiscal_position_id

        ctx = dict(self._context)
        ctx['pos_order_id'] = active_ids
        ctx['active_ids'] = order.picking_id.ids
        ctx['active_id'] = order.picking_id.id
        ctx['contact_display'] = 'partner_address'
        ctx['search_disable_custom_filters'] = True

        form = self.env.ref('stock.view_stock_return_picking_form', False)

        return self._open_return_view(form, ctx)
