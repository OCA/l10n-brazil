# -*- encoding: utf-8 -*-
#################################################################################
#                                                                               #
# Copyright (C) 2009  Renato Lima - Akretion, Gabriel C. Stabel                 #
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
from datetime import datetime
from dateutil.relativedelta import relativedelta

from osv import osv, fields
import netsvc
import pooler
from tools.translate import _
import decimal_precision as dp
from osv.orm import browse_record, browse_null

class purchase_order(osv.osv):
    
    _inherit = 'purchase.order'

    def _amount_all(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        cur_obj=self.pool.get('res.currency')
        for order in self.browse(cr, uid, ids, context=context):
            res[order.id] = {
                'amount_untaxed': 0.0,
                'amount_tax': 0.0,
                'amount_total': 0.0,
            }
            val = val1 = 0.0
            cur = order.pricelist_id.currency_id
            for line in order.order_line:
                val1 += line.price_subtotal
                for c in self.pool.get('account.tax').compute_all(cr, uid, line.taxes_id, line.price_unit, line.product_qty, order.partner_address_id.id, line.product_id.id, order.partner_id)['taxes']:
                    tax_brw = self.pool.get('account.tax').browse(cr, uid, c['id'])
                    if not tax_brw.tax_code_id.tax_discount:
                        val += c.get('amount', 0.0)
            res[order.id]['amount_tax']=cur_obj.round(cr, uid, cur, val)
            res[order.id]['amount_untaxed']=cur_obj.round(cr, uid, cur, val1)
            res[order.id]['amount_total']=res[order.id]['amount_untaxed'] + res[order.id]['amount_tax']
        return res
    
    def _get_order(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('purchase.order.line').browse(cr, uid, ids, context=context):
            result[line.order_id.id] = True
        return result.keys()
    
    _columns = {
                'fiscal_operation_category_id': fields.many2one('l10n_br_account.fiscal.operation.category',
                                                                'Categoria', domain="[('type','=','input'),('use_purchase','=',True)]" ),
                'fiscal_operation_id': fields.many2one('l10n_br_account.fiscal.operation', 'Operação Fiscal',
                                                       domain="[('fiscal_operation_category_id','=',fiscal_operation_category_id),(type,'=','input'),('use_purchase','=',True)]"),
                'amount_untaxed': fields.function(_amount_all, method=True, digits_compute= dp.get_precision('Purchase Price'),
                                                  string='Untaxed Amount', store={'purchase.order.line': (_get_order, None, 10),},
                                                  multi="sums", help="The amount without tax"),
                'amount_tax': fields.function(_amount_all, method=True, digits_compute= dp.get_precision('Purchase Price'), 
                                              string='Taxes', store={'purchase.order.line': (_get_order, None, 10),}, 
                                              multi="sums", help="The tax amount"),
                'amount_total': fields.function(_amount_all, method=True, digits_compute= dp.get_precision('Purchase Price'),
                                                string='Total', store={'purchase.order.line': (_get_order, None, 10),},
                                                multi="sums",help="The total amount"),
                }
    
    def _default_fiscal_operation_category(self, cr, uid, context=None):

        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)

        return user.company_id and user.company_id.purchase_fiscal_category_operation_id and user.company_id.purchase_fiscal_category_operation_id.id or False
    
    _defaults = {
                'fiscal_operation_category_id': _default_fiscal_operation_category,
                }

    
    def _fiscal_position_map(self, cr, uid, ids, partner_id, partner_invoice_id, company_id, fiscal_operation_category_id):

        obj_fiscal_position_rule = self.pool.get('account.fiscal.position.rule')
	    
        result = obj_fiscal_position_rule.fiscal_position_map(cr, uid, partner_id, partner_invoice_id, company_id, \
                                                              fiscal_operation_category_id, \
                                                              context={'use_domain': ('use_purchase', '=', True)})

        return result
        
    def onchange_partner_id(self, cr, uid, ids, partner_id=False, partner_address_id=False, \ 
                            company_id=False, fiscal_operation_category_id=False):

        result = super(purchase_order, self ).onchange_partner_id(cr, uid, ids, partner_id, company_id)

        if result['value']['partner_address_id']:
            partner_address_id = result['value']['partner_address_id']

        fiscal_data = self._fiscal_position_map(cr, uid, ids,partner_id, partner_address_id, company_id, fiscal_operation_category_id)
        
        result['value'].update(fiscal_data)

        return result


    def onchange_partner_address_id(self, cr, uid, ids, partner_id=False, partner_address_id=False, \
                                    company_id=False, fiscal_operation_category_id=False):
        
        result = super(purchase_order, self ).onchange_partner_address_id(cr, uid, ids, partner_address_id, company_id)

        fiscal_data = self._fiscal_position_map(cr, uid, ids, partner_id, partner_address_id, company_id, fiscal_operation_category_id)

        result['value'].update(fiscal_data)

        return result


    def onchange_fiscal_operation_category_id(self, cr, uid, ids, partner_id=False, partner_address_id=False, \ 
                                              company_id=False, fiscal_operation_category_id=False):
        
        result = {'value': {}}

        fiscal_data = self._fiscal_position_map(cr, uid, ids, partner_id, partner_address_id, company_id, fiscal_operation_category_id)

        result['value'].update(fiscal_data)

        return result
    
    def action_invoice_create(self, cr, uid, ids, *args):
        
        res = super(purchase_order, self).action_invoice_create(cr, uid, ids, *args)

        if not res: 
            return res
        
        for order in self.browse(cr, uid, ids):
            for order_line in order.order_line: 
                for inv_line in order_line.invoice_lines: 
                
                    invoice_id = inv_line.invoice_id
                    
                    fiscal_operation_id = order_line.fiscal_operation_id or order.fiscal_operation_id 
                    fiscal_operation_category_id = order_line.fiscal_operation_category_id or order.fiscal_operation_category_id

                    if invoice_id == inv_line.invoice_id:
                        for invoice in order.invoice_ids:
                        
                            if invoice.state in ('draft'):
                                company_id = self.pool.get('res.company').browse(cr, uid,order.company_id.id)
                                if not company_id.document_serie_product_ids:
                                    raise osv.except_osv(_('No fiscal document serie found !'),_("No fiscal document serie found for selected company %s and fiscal operation: '%s'") % (order.company_id.name, order.fiscal_operation_id.code))
                                comment = ''
                                if picking.fiscal_operation_id.inv_copy_note:
                                    comment = picking.fiscal_operation_id.note
                                self.pool.get('account.invoice').write(cr, uid, invoice_id.id, {'fiscal_operation_category_id': fiscal_operation_category_id.id, 
                                                                                                'fiscal_operation_id': order.fiscal_operation_id, 
                                                                                                'fiscal_document_id': fiscal_operation_id.fiscal_document_id.id, 
                                                                                                'document_serie_id': company_id.document_serie_product_ids[0].id, 
                                                                                                'own_invoice': False,
                                                                                                'comment': comment})

                            invoice_id = inv_line.invoice_id
                    
                    
                    self.pool.get('account.invoice.line').write(cr, uid, inv_line.id, {
                                                                                       'fiscal_operation_category_id': fiscal_operation_category_id.id, 
                                                                                       'fiscal_operation_id': fiscal_operation_id.id, 
                                                                                       'cfop_id': fiscal_operation_id.cfop_id.id})   
                    
        return res
        
        
        for order in self.browse(cr, uid, ids):
            for invoice in order.invoice_ids:
                if invoice.state in ('draft') and order.fiscal_operation_id:
                    #doc_serie_id = self.pool.get('l10n_br_account.document.serie').search(cr, uid,[('fiscal_document_id','=', order.fiscal_operation_id.fiscal_document_id.id),('active','=',True),('company_id','=',order.company_id.id)])
                    #if not doc_serie_id:
                    #    raise osv.except_osv(_('Nenhuma série de documento fiscal !'),_("Não existe nenhuma série de documento fiscal cadastrada para empresa:  '%s'") % (order.company_id.name,))
                    self.pool.get('account.invoice').write(cr, uid, invoice.id, {'fiscal_operation_category_id': order.fiscal_operation_category_id.id, 'fiscal_operation_id': order.fiscal_operation_id.id, 'fiscal_document_id': order.fiscal_operation_id.fiscal_document_id.id, 'fiscal_position': order.fiscal_position.id})
                    for inv_line in invoice.invoice_line:
                        self.pool.get('account.invoice.line').write(cr, uid, inv_line.id, {'cfop_id': order.fiscal_operation_id.cfop_id.id})

        return res
    
    def action_picking_create(self,cr, uid, ids, *args):

        picking_id = False

        for order in self.browse(cr, uid, ids):

            picking_id = super(purchase_order, self).action_picking_create(cr, uid, ids, *args)
            self.pool.get('stock.picking').write(cr, uid, picking_id, {'fiscal_operation_category_id': order.fiscal_operation_category_id.id, 'fiscal_operation_id': order.fiscal_operation_id.id, 'fiscal_position': order.fiscal_position.id})
        
        return picking_id
    
purchase_order()

class purchase_order_line(osv.osv):
    
    _inherit = 'purchase.order.line'

    _columns = {
                'fiscal_operation_category_id': fields.many2one('l10n_br_account.fiscal.operation.category', 'Categoria',
                                                                domain="[('type','=','input'),('use_purchase','=',True)]"),
                'fiscal_operation_id': fields.many2one('l10n_br_account.fiscal.operation', 'Operação Fiscal',
                                                       domain="[('fiscal_operation_category_id','=',fiscal_operation_category_id),('type','=','input'),('use_purchase','=',True)]" ),
                'fiscal_position': fields.many2one('account.fiscal.position', 'Fiscal Position', readonly=True,
                                                   domain="[('fiscal_operation_id','=',fiscal_operation_id)]", 
                                                   states={'draft':[('readonly',False)]}),
                }

    def product_id_change(self, cr, uid, ids, pricelist, product, qty, uom,
                          partner_id, date_order=False, fiscal_position=False, date_planned=False,
                          name=False, price_unit=False, notes=False, context={}, fiscal_operation_category_id=False,
                          fiscal_operation_id=False):
        
        result = super(purchase_order_line, self).product_id_change(cr, uid, ids, pricelist, product, qty, uom,
                                                                    partner_id, date_order, fiscal_position, 
                                                                    date_planned, name, price_unit, notes)

        if fiscal_operation_category_id:
            result['value']['fiscal_operation_category_id'] = fiscal_operation_category_id
            
        if fiscal_operation_id:
            result['value']['fiscal_operation_id'] = fiscal_operation_id
            
        if fiscal_position:
            result['value']['fiscal_position'] = fiscal_position
        
        return result

purchase_order_line()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
