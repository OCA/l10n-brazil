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

import time 
import netsvc
import decimal_precision as dp
from osv import fields, osv
import pooler
from tools import config
from tools.translate import _

##############################################################################
# Pedido de venda customizado
##############################################################################
class sale_order(osv.osv):
    
    _inherit = 'sale.order'
    
    def onchange_partner_id(self, cr, uid, ids, part, shop_id, fiscal_operation_category_id):

        result = super(sale_order, self).onchange_partner_id(cr, uid, ids, part, shop_id)
        result['value']['fiscal_position'] = False

        if not part or not shop_id:
            return {'value': {'partner_invoice_id': False, 'partner_shipping_id': False, 'partner_order_id': False, 'payment_term': False, 'fiscal_position': False, 'fiscal_operation_id': False}}
        
        obj_partner = self.pool.get('res.partner').browse(cr, uid, part)
        fiscal_position = obj_partner.property_account_position.id
        partner_fiscal_type = obj_partner.partner_fiscal_type_id.id
        
        if fiscal_position:
            result['value']['fiscal_position'] = fiscal_position
            result['value']['fiscal_operation_id'] = obj_partner.property_account_position.fiscal_operation_id.id
            return result

        obj_shop = self.pool.get('sale.shop').browse(cr, uid, shop_id)

        company_addr = self.pool.get('res.partner').address_get(cr, uid, [obj_shop.company_id.partner_id.id], ['default'])
        company_addr_default = self.pool.get('res.partner.address').browse(cr, uid, [company_addr['default']])[0]
        
        from_country = company_addr_default.country_id.id
        from_state = company_addr_default.state_id.id        

        partner_addr_default = self.pool.get('res.partner.address').browse(cr, uid, [result['value']['partner_invoice_id']])[0]

        to_country = partner_addr_default.country_id.id
        to_state = partner_addr_default.state_id.id
        
        fsc_pos_id = self.pool.get('account.fiscal.position.rule').search(cr, uid, [('company_id','=', obj_shop.company_id.id),('from_country','=',from_country),('from_state','=',from_state),('to_country','=',to_country),('to_state','=',to_state),('use_sale','=',True),('fiscal_operation_category_id','=',fiscal_operation_category_id),('partner_fiscal_type_id','=',partner_fiscal_type)])
        if not fsc_pos_id:
            fsc_pos_id = self.pool.get('account.fiscal.position.rule').search(cr, uid, [('company_id','=', obj_shop.company_id.id),('from_country','=',from_country),('from_state','=',from_state),('to_country','=',to_country),('to_state','=',to_state),('use_sale','=',True),('fiscal_operation_category_id','=',fiscal_operation_category_id)])
        
        if fsc_pos_id:
            obj_fpo_rule = self.pool.get('account.fiscal.position.rule').browse(cr, uid, fsc_pos_id)[0]
            result['value']['fiscal_position'] = obj_fpo_rule.fiscal_position_id.id
            result['value']['fiscal_operation_id'] = obj_fpo_rule.fiscal_position_id.fiscal_operation_id.id
        
        return result
    
    def onchange_partner_invoice_id(self, cr, uid, ids, ptn_invoice_id, ptn_id, shop_id, fiscal_operation_category_id):
        
        result = super(sale_order, self).onchange_partner_invoice_id(cr, uid, ids, ptn_invoice_id, ptn_id, shop_id)
        result['value']['fiscal_position'] = False

        if not shop_id or not ptn_invoice_id or not ptn_id or not fiscal_operation_category_id:
            return result
  
        partner = self.pool.get('res.partner').browse(cr, uid, ptn_id)
        fiscal_position = partner.property_account_position.id or False
        partner_fiscal_type = partner.partner_fiscal_type_id.id

        if fiscal_position:
            result['value']['fiscal_position'] = fiscal_position
            result['value']['fiscal_operation_id'] = obj_partner.property_account_position.fiscal_operation_id.id
            return result

        obj_shop = self.pool.get('sale.shop').browse(cr, uid, shop_id)

        company_addr = self.pool.get('res.partner').address_get(cr, uid, [obj_shop.company_id.partner_id.id], ['default'])
        company_addr_default = self.pool.get('res.partner.address').browse(cr, uid, [company_addr['default']])[0]

        from_country = company_addr_default.country_id.id
        from_state = company_addr_default.state_id.id
        
        partner_addr_invoice = self.pool.get('res.partner.address').browse(cr, uid, [ptn_invoice_id])[0]
        
        to_country = partner_addr_invoice.country_id.id
        to_state = partner_addr_invoice.state_id.id
        
        
        fsc_pos_id = self.pool.get('account.fiscal.position.rule').search(cr, uid, [('company_id','=',obj_shop.company_id.id), ('from_country','=',from_country),('from_state','=',from_state),('to_country','=',to_country),('to_state','=',to_state),('use_sale','=',True),('fiscal_operation_category_id','=',fiscal_operation_category_id),('partner_fiscal_type_id','=',partner_fiscal_type)])
        if fsc_pos_id:
            fsc_pos_id = self.pool.get('account.fiscal.position.rule').search(cr, uid, [('company_id','=',obj_shop.company_id.id), ('from_country','=',from_country),('from_state','=',from_state),('to_country','=',to_country),('to_state','=',to_state),('use_sale','=',True),('fiscal_operation_category_id','=',fiscal_operation_category_id)])
        
        if fsc_pos_id:
            obj_fpo_rule = self.pool.get('account.fiscal.position.rule').browse(cr, uid, fsc_pos_id)[0]
            result['value']['fiscal_position'] = obj_fpo_rule.fiscal_position_id.id
            result['value']['fiscal_operation_id'] = obj_fpo_rule.fiscal_position_id.fiscal_operation_id.id

        return result

    def onchange_shop_id(self, cr, uid, ids, shop_id, ptn_id=False, ptn_invoice_id=False):
        
        result = super(sale_order, self).onchange_shop_id(cr, uid, ids, shop_id, ptn_id)
        result['value']['fiscal_position'] = False
        result['value']['fiscal_operation_id'] = False
        
        if not shop_id:
            result['value']['fiscal_operation_category_id'] = False
            return result
        
        obj_shop = self.pool.get('sale.shop').browse(cr, uid, shop_id)        
        fiscal_operation_category_id = obj_shop.default_fo_category_id.id        
        result['value']['fiscal_operation_category_id'] = fiscal_operation_category_id
        
        if not ptn_id or not ptn_invoice_id:
            return result
        
        obj_partner = self.pool.get('res.partner').browse(cr, uid, ptn_id)
        fiscal_position = obj_partner.property_account_position.id
        partner_fiscal_type = obj_partner.partner_fiscal_type_id.id
        
        if fiscal_position:
            result['value']['fiscal_position'] = fiscal_position
            result['value']['fiscal_operation_id'] = obj_partner.property_account_position.fiscal_operation_id.id
            return result

        obj_shop = self.pool.get('sale.shop').browse(cr, uid, shop_id)

        company_addr = self.pool.get('res.partner').address_get(cr, uid, [obj_shop.company_id.partner_id.id], ['default'])
        company_addr_default = self.pool.get('res.partner.address').browse(cr, uid, [company_addr['default']])[0]
        
        from_country = company_addr_default.country_id.id
        from_state = company_addr_default.state_id.id        

        partner_addr_default = self.pool.get('res.partner.address').browse(cr, uid, [ptn_invoice_id])[0]

        to_country = partner_addr_default.country_id.id
        to_state = partner_addr_default.state_id.id
            
        fsc_pos_id = self.pool.get('account.fiscal.position.rule').search(cr, uid, [('company_id','=', obj_shop.company_id.id),('from_country','=',from_country),('from_state','=',from_state),('to_country','=',to_country),('to_state','=',to_state),('use_sale','=',True),('fiscal_operation_category_id','=',fiscal_operation_category_id),('partner_fiscal_type_id','=',partner_fiscal_type)])
        if fsc_pos_id:
            fsc_pos_id = self.pool.get('account.fiscal.position.rule').search(cr, uid, [('company_id','=', obj_shop.company_id.id),('from_country','=',from_country),('from_state','=',from_state),('to_country','=',to_country),('to_state','=',to_state),('use_sale','=',True),('fiscal_operation_category_id','=',fiscal_operation_category_id)])
        
        if fsc_pos_id:
            obj_fpo_rule = self.pool.get('account.fiscal.position.rule').browse(cr, uid, fsc_pos_id)[0]
            result['value']['fiscal_position'] = obj_fpo_rule.fiscal_position_id.id
            result['value']['fiscal_operation_id'] = obj_fpo_rule.fiscal_position_id.fiscal_operation_id.id
        
        return result
    
    def action_invoice_create(self, cr, uid, ids, grouped=False, states=['confirmed', 'done', 'exception'], date_inv = False, context=None):
        
        result = super(sale_order, self).action_invoice_create(cr, uid, ids, grouped, states, date_inv, context)

        if not result: 
            return result

        for order in self.browse(cr, uid, ids):
            for invoice in order.invoice_ids:
                if invoice.state in ('draft') and order.fiscal_operation_id:
                    doc_serie_id = self.pool.get('l10n_br_account.document.serie').search(cr, uid,[('fiscal_document_id','=', order.fiscal_operation_id.fiscal_document_id.id),('active','=',True),('company_id','=',order.company_id.id)])
                    if not doc_serie_id:
                        raise osv.except_osv(_('No fiscal document serie found !'),_("No fiscal document serie found for selected company %s and fiscal operation: '%s'") % (order.company_id.name, order.fiscal_operation_id.code))
                    self.pool.get('account.invoice').write(cr, uid, invoice.id, {'fiscal_operation_category_id': order.fiscal_operation_category_id.id, 'fiscal_operation_id': order.fiscal_operation_id.id, 'cfop_id': order.fiscal_operation_id.cfop_id.id, 'fiscal_document_id': order.fiscal_operation_id.fiscal_document_id.id, 'document_serie_id': doc_serie_id[0]})
                    for inv_line in invoice.invoice_line:
                        self.pool.get('account.invoice.line').write(cr, uid, inv_line.id, {'cfop_id': order.fiscal_operation_id.cfop_id.id})

        return result
    
    def action_ship_create(self, cr, uid, ids, *args):
   
        result = super(sale_order, self).action_ship_create(cr, uid, ids, *args)
        
        for order in self.browse(cr, uid, ids, context={}):
            for picking in order.picking_ids:
                self.pool.get('stock.picking').write(cr, uid, picking.id, {'fiscal_operation_category_id': order.fiscal_operation_category_id.id, 'fiscal_operation_id': order.fiscal_operation_id.id, 'fiscal_position': order.fiscal_position.id})
        
        return result
            
    def _amount_all(self, cr, uid, ids, field_name, arg, context):
        res = super(sale_order, self)._amount_all(cr, uid, ids, field_name, arg, context)
        
        #Não é mostrado valores de impostos na ordem de venda
        for order in self.browse(cr, uid, ids):
            res[order.id]['amount_tax'] = 0
            res[order.id]['amount_total'] = res[order.id]['amount_untaxed'] + res[order.id]['amount_tax']
            
        return res

    def _get_order(self, cr, uid, ids, context={}):
        result = super(sale_order, self)._get_order(cr, uid, ids, context)
        return result.keys()

    _columns = {
                'fiscal_operation_category_id': fields.many2one('l10n_br_account.fiscal.operation.category', 'Categoria'),
                'fiscal_operation_id': fields.many2one('l10n_br_account.fiscal.operation', 'Operação Fiscal', domain="[('fiscal_operation_category_id','=',fiscal_operation_category_id)]" ),
                'amount_untaxed': fields.function(_amount_all, method=True, digits_compute= dp.get_precision('Sale Price'), string='Untaxed Amount',
                store = {
                         'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line'], 10),
                         'sale.order.line': (_get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty'], 10),
                         },
                multi='sums'),
                'amount_tax': fields.function(_amount_all, method=True, digits_compute= dp.get_precision('Sale Price'), string='Taxes',
                store = {
                         'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line'], 10),
                         'sale.order.line': (_get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty'], 10),
                         },
                multi='sums'),
                'amount_total': fields.function(_amount_all, method=True, digits_compute= dp.get_precision('Sale Price'), string='Total',
                store = {
                'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line'], 10),
                         'sale.order.line': (_get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty'], 10),
                         },
                multi='sums'),
               }
    
sale_order()

##############################################################################
# Linha da Ordem de Venda Customizada
##############################################################################
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
    
##############################################################################
# Estabelecimento Customizado
##############################################################################
class sale_shop(osv.osv):
    
    _inherit = 'sale.shop'
    _columns = {
                'default_fo_category_id': fields.many2one('l10n_br_account.fiscal.operation.category', 'Categoria Fiscal Padrão'),
    }

sale_shop()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
