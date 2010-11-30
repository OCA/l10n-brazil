# -*- encoding: utf-8 -*-
#################################################################################
#                                                                               #
# Copyright (C) 2009  Renato Lima - Akretion                                    #
#                                                                               #
#This program is free software: you can redistribute it and/or modify           #
#it under the terms of the GNU General Public License as published by           #
#the Free Software Foundation, either version 3 of the License, or              #
#(at your option) any later version.                                            #
#                                                                               #
#This program is distributed in the hope that it will be useful,                #
#but WITHOUT ANY WARRANTY; without even the implied warranty of                 #
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the                  #
#GNU General Public License for more details.                                   #
#                                                                               #
#You should have received a copy of the GNU General Public License              #
#along with this program.  If not, see <http://www.gnu.org/licenses/>.          #
#################################################################################

from osv import osv, fields

class stock_picking(osv.osv):
    _inherit = "stock.picking"
    _description = "Picking List"
    _columns = {
        'vehicle_id': fields.many2one('delivery.carrier.vehicle', 'Veículo', select=True, required=True, domain="[('carrier_id','=',carrier_id)]"),
    }

    def _invoice_line_hook(self, cr, uid, move_line, invoice_line_id):
        '''Call after the creation of the invoice line'''

        self.pool.get('account.invoice.line').write(cr, uid, invoice_line_id, {'cfop_id': move_line.picking_id.fiscal_operation_id.cfop_id.id})

        return super(stock_picking, self)._invoice_line_hook(cr, uid, move_line, invoice_line_id)

    def _invoice_hook(self, cr, uid, picking, invoice_id):
        '''Call after the creation of the invoice'''

        self.pool.get('account.invoice').write(cr, uid, invoice_id, {'fiscal_operation_category_id': picking.fiscal_operation_category_id.id, 'fiscal_operation_id': picking.fiscal_operation_id.id, 'cfop_id': picking.fiscal_operation_id.cfop_id.id, 'fiscal_document_id': picking.fiscal_operation_id.fiscal_document_id.id, 'fiscal_position': picking.fiscal_position.id, 'carrier_id': picking.carrier_id, 'weight': picking.weight, 'weight_net': picking.weight_net, 'number_of_packages': picking.number_of_packages})

        return super(stock_picking, self)._invoice_hook(cr, uid, picking, invoice_id)

stock_picking()