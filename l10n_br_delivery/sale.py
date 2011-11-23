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
                              states=['confirmed', 'done', 'exception'], date_inv = False, context=None):
        
        result = super(sale_order, self).action_invoice_create(cr, uid, ids, grouped, states, date_inv, context)
        
        if not result: 
            return result
    
        for order in self.browse(cr, uid, ids):
            for invoice in order.invoice_ids:
                if invoice.state in ('draft') and order.fiscal_operation_id:
                    doc_serie_id = self.pool.get('l10n_br_account.document.serie').search(cr, uid,[('fiscal_document_id','=', order.fiscal_operation_id.fiscal_document_id.id),('active','=',True),('company_id','=',order.company_id.id)])
                    if not doc_serie_id:
                        raise osv.except_osv(_('Nenhuma série de documento fiscal !'),_("Não existe nenhuma série de documento fiscal cadastrada para empresa:  '%s'") % (order.company_id.name,))
                    
                    self.pool.get('account.invoice').write(cr, uid, invoice.id, {
                                                                                 'partner_shipping_id': order.partner_shipping_id.id,
                                                                                 'fiscal_operation_category_id': order.fiscal_operation_category_id.id, 
                                                                                 'fiscal_operation_id': order.fiscal_operation_id.id, 
                                                                                 'cfop_id': order.fiscal_operation_id.cfop_id.id, 
                                                                                 'fiscal_document_id': order.fiscal_operation_id.fiscal_document_id.id, 
                                                                                 'document_serie_id': doc_serie_id[0], 
                                                                                 'carrier_id': order.carrier_id.id,
                                                                                 'incoterm': order.incoterm.id
                                                                                 })
                    for inv_line in invoice.invoice_line:
                        self.pool.get('account.invoice.line').write(cr, uid, inv_line.id, {'cfop_id': order.fiscal_operation_id.cfop_id.id})

        return result
    
    def action_ship_create(self, cr, uid, ids, *args):
   
        result = super(sale_order, self).action_ship_create(cr, uid, ids, *args)
        
        for order in self.browse(cr, uid, ids, context={}):
            for picking in order.picking_ids:
                self.pool.get('stock.picking').write(cr, uid, picking.id, {'incoterm': order.incoterm.id})
        
        return result
    
sale_order()

class sale_order_line(osv.osv):
    
    _inherit = 'sale.order.line'
    
    def create_sale_order_line_invoice(self, cr, uid, ids, context=None):
        result = super(sale_order_line, self).create_sale_order_line_invoice(cr, uid, ids, context)
        inv_ids = []
        if result:

            for so_line in self.browse(cr, uid, ids):
                for inv_line in so_line.invoice_lines:
                    if inv_line.invoice_id.state in ('draft'):
                        if inv_line.invoice_id.id not in inv_ids: 
                            inv_ids.append(inv_line.id)
                            self.pool.get('account.invoice').write(cr, uid, inv_line.invoice_id.id, {'fiscal_operation_category_id': so_line.order_id.fiscal_operation_category_id.id, 'fiscal_operation_id': so_line.order_id.fiscal_operation_id.id, 'cfop_id': so_line.order_id.fiscal_operation_id.cfop_id.id, 'fiscal_document_id': so_line.order_id.fiscal_operation_id.fiscal_document_id.id})
                        self.pool.get('account.invoice.line').write(cr, uid, inv_line.id, {'cfop_id': so_line.order_id.fiscal_operation_id.cfop_id.id})
            
            
            
        return result

sale_order_line()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
