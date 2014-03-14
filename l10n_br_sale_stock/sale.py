# -*- encoding: utf-8 -*-
###############################################################################
#                                                                             #
# Copyright (C) 2013  Raphaël Valyi - Akretion                                #
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

from openerp.osv import orm
from openerp.tools.translate import _


class SaleOrder(orm.Model):
    _inherit = 'sale.order'

    def _prepare_order_picking(self, cr, uid, order, context=None):
        result = super(SaleOrder, self)._prepare_order_picking(cr, uid,
            order, context)
        result['fiscal_category_id'] = order.fiscal_category_id and \
        order.fiscal_category_id.id
        result['fiscal_position'] = order.fiscal_position and \
        order.fiscal_position.id
        return result

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
        #TODO - Testar se só sobrescrevendo o metodo _fiscal_comment nao precisa fazer isso

        comment = []
        fiscal_comment = self._fiscal_comment(cr, uid, order, context=context)
        result['comment'] = " - ".join(comment + fiscal_comment)
        return result


class SaleOrderLine(orm.Model):
    _inherit = 'sale.order.line'

    def _prepare_order_line_invoice_line(self, cr, uid, line,
                                         account_id=False, context=None):
        result = super(SaleOrderLine, self)._prepare_order_line_invoice_line(
            cr, uid, line, account_id, context)

        if line.product_id.fiscal_type == 'product':
            cfop = self.pool.get("account.fiscal.position").read(
                cr, uid, [result['fiscal_position']], ['cfop_id'],
                context=context)
            if cfop[0]['cfop_id']:
                result['cfop_id'] = cfop[0]['cfop_id'][0]
        return result
