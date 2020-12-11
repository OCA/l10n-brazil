# -*- encoding: utf-8 -*-
#################################################################################
#                                                                               #
# Copyright (C) 2009  Renato Lima - Akretion                                    #
#                                                                               #
#This program is free software: you can redistribute it and/or modify           #
#it under the terms of the GNU Affero General Public License as published by    #
#the Free Software Foundation, either version 3 of the License, or              #
#(at your option) any later version.                                            #
#                                                                               #
#This program is distributed in the hope that it will be useful,                #
#but WITHOUT ANY WARRANTY; without even the implied warranty of                 #
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the                  #
#GNU Affero General Public License for more details.                            #
#                                                                               #
#You should have received a copy of the GNU Affero General Public License       #
#along with this program.  If not, see <http://www.gnu.org/licenses/>.          #
#################################################################################

from osv import osv, fields

class stock_picking(osv.osv):
    
    _inherit = "stock.picking"
    _description = "Picking List"

    _columns = {
                'vehicle_id': fields.many2one('l10n_br_delivery.carrier.vehicle', 'Veículo'),
                'incoterm': fields.many2one('stock.incoterms', 'Tipo do Frete', 
                                            help="Incoterm which stands for 'International Commercial terms' implies its a series of sales terms which are used in the commercial transaction."),
                }

    def _invoice_hook(self, cr, uid, picking, invoice_id):
        '''Call after the creation of the invoice'''

        self.pool.get('account.invoice').write(cr, uid, invoice_id, {
                                                                     'partner_shipping_id': picking.address_id.id,
                                                                     'fiscal_operation_category_id': picking.fiscal_operation_category_id.id, 
                                                                     'fiscal_operation_id': picking.fiscal_operation_id.id, 
                                                                     'cfop_id': picking.fiscal_operation_id.cfop_id.id, 
                                                                     'fiscal_document_id': picking.fiscal_operation_id.fiscal_document_id.id, 
                                                                     'fiscal_position': picking.fiscal_position.id,
                                                                     'carrier_id': picking.carrier_id.id,
                                                                     'vehicle_id': picking.vehicle_id.id,
                                                                     'incoterm': picking.incoterm.id,
                                                                     'weight': picking.weight, 
                                                                     'weight_net': picking.weight_net, 
                                                                     'number_of_packages': picking.number_of_packages
                                                                     })

        return super(stock_picking, self)._invoice_hook(cr, uid, picking, invoice_id)

stock_picking()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
