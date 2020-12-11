# -*- coding: utf-8 -*-
###############################################################################
#                                                                             #
# Copyright (C) 2009  Renato Lima - Akretion                                  #
#                                                                             #
# This program is free software: you can redistribute it and/or modify        #
# it under the terms of the GNU Affero General Public License as published by #
# the Free Software Foundation, either version 3 of the License, or           #
# (at your option) any later version.                                         #
#                                                                             #
# This program is distributed in the hope that it will be useful,             #
# but WITHOUT ANY WARRANTY; without even the implied warranty of              #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the               #
# GNU Affero General Public License for more details.                         #
#                                                                             #
# You should have received a copy of the GNU Affero General Public License    #
# along with this program.  If not, see <http://www.gnu.org/licenses/>.       #
###############################################################################

import time

from openerp import models, api, _
from openerp.exceptions import except_orm


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.model
    def _prepare_invoice(self, order, lines):
        """Prepare the dict of values to create the new invoice for a
           sale order. This method may be overridden to implement custom
           invoice generation (making sure to call super() to establish
           a clean extension chain).

           :param browse_record order: sale.order record to invoice
           :param list(int) line: list of invoice line IDs that must be
                                  attached to the invoice
           :return: dict of value to create() the invoice
        """
        result = super(SaleOrder, self)._prepare_invoice(order, lines)

        if order.carrier_id:
            result['carrier_id'] = order.carrier_id.id

        return result

    # TODO Inplement this in object stock.move method _picking_assign
    # def _prepare_order_picking(self, cr, uid, order, context=None):
    #    result = super(SaleOrder, self)._prepare_order_picking(
    #        cr, uid, order, context)
    #
    #    # FIXME - Confirmado bug do OpenERP
    #    # https://bugs.launchpad.net/bugs/1161138
    #    # Esse campo já deveria ser copiado pelo módulo nativo delivery
    #    result['incoterm'] = order.incoterm and order.incoterm.id or False
    #    return result

    # TODO migrate to new API
    def delivery_set(self, cr, uid, ids, context=None):
        # Copia do modulo delivery
        # Exceto pelo final que adiciona ao campo total do frete.
        grid_obj = self.pool.get('delivery.grid')
        carrier_obj = self.pool.get('delivery.carrier')

        for order in self.browse(cr, uid, ids, context=context):
            grid_id = carrier_obj.grid_get(cr, uid, [order.carrier_id.id],
                                           order.partner_shipping_id.id)

            if not grid_id:
                raise except_orm(_('No Grid Available!'),
                                 _('No grid matching for this carrier!'))

            if order.state not in ('draft'):
                raise except_orm(_('Order not in Draft State!'),
                                 _('The order state have to be draft \
                                   to add delivery lines.'))

            grid = grid_obj.browse(cr, uid, grid_id, context=context)

            amount_freight = grid_obj.get_price(cr, uid, grid.id, order,
                                                time.strftime('%Y-%m-%d'),
                                                context)
            self.onchange_amount_freight(cr, uid, ids, amount_freight)
        return self.write(cr, uid, ids, {'amount_freight': amount_freight})
