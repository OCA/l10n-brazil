# -*- encoding: utf-8 -*-
###############################################################################
#                                                                             #
# Copyright (C) 2009  Renato Lima - Akretion                                  #
# Copyright (C) 2012  Raphaël Valyi - Akretion                                #
#                                                                             #
#This program is free software: you can redistribute it and/or modify         #
#it under the terms of the GNU Affero General Public License as published by  #
#the Free Software Foundation, either version 3 of the License, or            #
#(at your option) any later version.                                          #
#                                                                             #
#This program is distributed in the hope that it will be useful,              #
#but WITHOUT ANY WARRANTY; without even the implied warranty of               #
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the                #
#GNU Affero General Public License for more details.                          #
#                                                                             #
#You should have received a copy of the GNU Affero General Public License     #
#along with this program.  If not, see <http://www.gnu.org/licenses/>.        #
###############################################################################

from osv import osv, fields
from openerp.tools.translate import _


class stock_incoterms(osv.Model):
    _inherit = 'stock.incoterms'
    _columns = {
        'freight_responsibility': fields.selection(
            [('0', 'Emitente'),
            ('1', 'Destinatário'),
            ('2', 'Terceiros'),
            ('9', 'Sem Frete')],
            'Frete por Conta', required=True)
    }
    _defaults = {
        'freight_responsibility': 0
    }


class stock_picking(osv.Model):
    _inherit = 'stock.picking'

    def _default_fiscal_category(self, cr, uid, context=None):
        user = self.pool.get('res.users').browse(
            cr, uid, uid, context=context)
        return user.company_id.stock_fiscal_category_id and \
        user.company_id.stock_fiscal_category_id.id

    _columns = {
        'fiscal_category_id': fields.many2one(
            'l10n_br_account.fiscal.category', 'Categoria'),
        'fiscal_position': fields.many2one(
            'account.fiscal.position', 'Posição Fiscal',
            domain="[('fiscal_category_id','=',fiscal_category_id)]")
    }
    _defaults = {
        'fiscal_category_id': _default_fiscal_category
    }

    def onchange_partner_in(self, cr, uid, ids, partner_id=None,
                            context=None, company_id=None,
                            fiscal_category_id=None):
        if not context:
            context = {}

        return super(stock_picking, self).onchange_partner_in(
            cr, uid, partner_id=partner_id, context=context,
            company_id=company_id, fiscal_category_id=fiscal_category_id)

    def onchange_fiscal_category_id(self, cr, uid, ids,
                                    partner_id, company_id=False,
                                    fiscal_category_id=False,
                                    context=None, **kwargs):
        if not context:
            context = {}

        result = {'value': {'fiscal_position': False}}

        if not partner_id or not company_id:
            return result

        partner_invoice_id = self.pool.get('res.partner').address_get(
            cr, uid, [partner_id], ['invoice'])['invoice']
        partner_shipping_id = self.pool.get('res.partner').address_get(
            cr, uid, [partner_id], ['delivery'])['delivery']

        kwargs = {
           'partner_id': partner_id,
           'partner_invoice_id': partner_invoice_id,
           'partner_shipping_id': partner_shipping_id,
           'company_id': company_id,
           'context': context,
           'fiscal_category_id': fiscal_category_id
        }

        return self._fiscal_position_map(cr, uid, ids, result, **kwargs)

    def _prepare_invoice_line(self, cr, uid, group, picking, move_line,
                              invoice_id, invoice_vals, context=None):
        result = super(stock_picking, self)._prepare_invoice_line(
            cr, uid, group, picking, move_line, invoice_id, invoice_vals,
            context)
        if move_line.sale_line_id:
            fiscal_position = move_line.sale_line_id.fiscal_position or \
            move_line.sale_line_id.order_id.fiscal_position
            fiscal_category_id = move_line.sale_line_id.fiscal_category_id or \
            move_line.sale_line_id.order_id.fiscal_category_id
            refund_fiscal_position = fiscal_category_id.refund_fiscal_category_id or False
        elif move_line.purchase_line_id:
            fiscal_position = move_line.purchase_line_id.fiscal_position or \
            move_line.purchase_line_id.order_id.fiscal_position
            fiscal_category_id = move_line.purchase_line_id.fiscal_category_id or move_line.purchase_line_id.order_id.fiscal_category_id
            refund_fiscal_position = fiscal_category_id.refund_fiscal_category_id or False
        else:
            fiscal_position = move_line.picking_id.fiscal_position
            fiscal_category_id = move_line.picking_id.fiscal_category_id

        if context.get('inv_type') in ('in_refund', 'out_refund'):
            if not refund_fiscal_position:
                raise osv.except_osv(
                    _('Error!'),
                    _("This Fiscal Operation does not has Fiscal Operation \
                    for Returns!"))

            fiscal_category_id = refund_fiscal_position
            fiscal_data = self._fiscal_position_map(
                cr, uid, move_line.picking_id.partner_id.id,
                move_line.picking_id.address_id.id,
                move_line.picking_id.company_id.id,
                fiscal_category_id.id)

            fiscal_position = self.pool.get('account.fiscal.position').browse(
                cr, uid, fiscal_data.get('fiscal_position', 0))

        result['cfop_id'] = fiscal_position and \
        fiscal_position.cfop_id and fiscal_position.cfop_id.id
        result['fiscal_category_id'] = fiscal_category_id and \
        fiscal_category_id.id
        result['fiscal_position'] = fiscal_position and \
        fiscal_position.id
        return result

    def _prepare_invoice(self, cr, uid, picking, partner,
                        inv_type, journal_id, context=None):
        result = super(stock_picking, self)._prepare_invoice(
            cr, uid, picking, partner, inv_type, journal_id, context)
        result['fiscal_category_id'] = picking.fiscal_category_id and \
        picking.fiscal_category_id.id
        result['fiscal_position'] = picking.fiscal_position and \
        picking.fiscal_position.id
        return result
