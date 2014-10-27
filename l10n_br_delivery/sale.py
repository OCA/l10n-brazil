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

from openerp import models, api


class SaleOrder(models.Model):
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

        return result

    # TODO não existe mais este método pai
    def _prepare_order_picking(self, cr, uid, order, context=None):
        result = super(SaleOrder, self)._prepare_order_picking(
            cr, uid, order, context)

        # FIXME - Confirmado bug do OpenERP
        # https://bugs.launchpad.net/bugs/1161138
        # Esse campo já deveria ser copiado pelo módulo nativo delivery
        result['incoterm'] = order.incoterm and order.incoterm.id or False
        return result

    # TODO
    def _prepare_order_line_move(self, cr, uid, order, line, picking_id, date_planned, context=None):
        result = super(SaleOrder, self)._prepare_order_line_move( cr, uid,
               order, line, picking_id, date_planned, context)
        result['fiscal_category_id'] = line.fiscal_category_id and \
        line.fiscal_category_id.id
        result['fiscal_position'] = line.fiscal_position and \
        line.fiscal_position.id
        return result
