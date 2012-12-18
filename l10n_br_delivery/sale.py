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
import netsvc
import decimal_precision as dp
from osv import fields, osv
import pooler
from tools import config
from tools.translate import _


class sale_order(osv.osv):
    _inherit = 'sale.order'

    def action_invoice_create(self, cr, uid, ids, grouped=False,
                              states=['confirmed', 'done', 'exception'],
                              date_inv = False, context=None):

        result = super(sale_order, self).action_invoice_create(
            cr, uid, ids, grouped, states, date_inv, context)

        if not result:
            return result

        for order in self.browse(cr, uid, ids):
            for invoice in order.invoice_ids:
                if invoice.state in ('draft'):
                    self.pool.get('account.invoice').write(
                        cr, uid, invoice.id, {
                            'partner_shipping_id': order.partner_shipping_id.id,
                            'carrier_id': order.carrier_id.id,
                            'incoterm': order.incoterm and order.incoterm.id or False})

        return result
    
    def action_ship_create(self, cr, uid, ids, *args):
        result = super(sale_order, self).action_ship_create(cr, uid, ids, *args)

        for order in self.browse(cr, uid, ids, context={}):
            for picking in order.picking_ids:
                self.pool.get('stock.picking').write(cr, uid, picking.id, {'incoterm': order.incoterm.id})

        return result

sale_order()

