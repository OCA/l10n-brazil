# -*- encoding: utf-8 -*-
###############################################################################
#                                                                             #
# Copyright (C) 2009  Renato Lima - Akretion                                  #
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

import time
from openerp.osv import orm, osv
from openerp.tools.translate import _


def  calc_price_ratio(price_gross, amount_calc, amount_total):
    return price_gross * amount_calc / amount_total


class SaleOrder(orm.Model):
    _inherit = 'sale.order'

    def _prepare_invoice(self, cr, uid, order, lines, context=None):
        """Prepare the dict of values to create the new invoice for a
           sale order. This method may be overridden to implement custom
           invoice generation (making sure to call super() to establish
           a clean extension chain).

           :param browse_record order: sale.order record to invoice
           :param list(int) line: list of invoice line IDs that must be
                                  attached to the invoice
           :return: dict of value to create() the invoice
        """
        result = super(SaleOrder, self)._prepare_invoice(
            cr, uid, order, lines, context)

        if order.carrier_id:
            result['carrier_id'] = order.carrier_id.id

        if order.incoterm:
            result['incoterm'] = order.incoterm.id
        return result

    def action_invoice_create(self, cr, uid, ids, grouped=False, states=None,
                            date_invoice=False, context=None):
        invoice_id = super(SaleOrder, self).action_invoice_create(
            cr, uid, ids, grouped, states, date_invoice, context)

        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        company = self.pool.get('res.company').browse(
            cr, uid, user.company_id.id, context=context)

        inv = self.pool.get("account.invoice").browse(
            cr, uid, invoice_id, context=context)
        vals = [
            ('Frete', company.account_freight_id, inv.amount_freight),
            ('Seguro', company.account_insurance_id, inv.amount_insurance),
            ('Outros Custos', company.account_other_costs, inv.amount_costs)
        ]

        ait_obj = self.pool.get('account.invoice.tax')
        for tax in vals:
            if tax[2] > 0:
                ait_obj.create(cr, uid,
                {
                 'invoice_id': invoice_id,
                 'name': tax[0],
                 'account_id': tax[1].id,
                 'amount': tax[2],
                 'base': tax[2],
                 'manual': 1,
                 'company_id': company.id,
                }, context=context)
        return invoice_id

    def _prepare_order_picking(self, cr, uid, order, context=None):
        result = super(SaleOrder, self)._prepare_order_picking(
            cr, uid, order, context)

        # FIXME - Confirmado bug do OpenERP
        # https://bugs.launchpad.net/bugs/1161138
        # Esse campo já deveria ser copiado pelo módulo nativo delivery
        result['incoterm'] = order.incoterm and order.incoterm.id or False
        return result

    def delivery_set(self, cr, uid, ids, context=None):
        #Copia do modulo delivery
        #Exceto pelo final que adiciona ao campo total do frete.
        grid_obj = self.pool.get('delivery.grid')
        carrier_obj = self.pool.get('delivery.carrier')

        for order in self.browse(cr, uid, ids, context=context):
            grid_id = carrier_obj.grid_get(cr, uid, [order.carrier_id.id],
            order.partner_shipping_id.id)

            if not grid_id:
                raise osv.except_osv(_('No Grid Available!'),
                     _('No grid matching for this carrier!'))

            if not order.state in ('draft'):
                raise osv.except_osv(_('Order not in Draft State!'),
                    _('The order state have to be draft to add delivery lines.'))

            grid = grid_obj.browse(cr, uid, grid_id, context=context)

            amount_freight = grid_obj.get_price(cr, uid, grid.id, order,
            time.strftime('%Y-%m-%d'), context)
            self.onchange_amount_freight(cr, uid, ids, amount_freight)
        return self.write(cr, uid, ids, {'amount_freight': amount_freight})

    def onchange_amount_freight(self, cr, uid, ids, amount_freight=False):
        result = {}
        if (amount_freight is False) or not ids:
            return {'value': {'amount_freight': 0.00}}

        line_obj = self.pool.get('sale.order.line')
        for order in self.browse(cr, uid, ids, context=None):
            for line in order.order_line:
                line_obj.write(cr, uid, [line.id], {'freight_value':
            calc_price_ratio(line.price_gross, amount_freight,
                order.amount_gross)}, context=None)
        return result

    def onchange_amount_insurance(self, cr, uid, ids, amount_insurance=False):
        result = {}
        if (amount_insurance is False) or not ids:
            return {'value': {'amount_insurance': 0.00}}

        line_obj = self.pool.get('sale.order.line')
        for order in self.browse(cr, uid, ids, context=None):
            for line in order.order_line:
                line_obj.write(cr, uid, [line.id], {'insurance_value':
          calc_price_ratio(line.price_gross, amount_insurance,
                order.amount_gross)}, context=None)
        return result

    def onchange_amount_costs(self, cr, uid, ids, amount_costs=False):
        result = {}
        if (amount_costs is False) or not ids:
            return {'value': {'amount_costs': 0.00}}

        line_obj = self.pool.get('sale.order.line')
        for order in self.browse(cr, uid, ids, context=None):
            for line in order.order_line:
                line_obj.write(cr, uid, [line.id], {'other_costs_value':
          calc_price_ratio(line.price_gross, amount_costs,
                order.amount_gross)}, context=None)
        return result
