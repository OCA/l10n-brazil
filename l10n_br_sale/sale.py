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
    
    def onchange_partner_id(self, cr, uid, ids, part, shop_id=False, fiscal_operation_category_id=False):

        result = super(sale_order, self).onchange_partner_id(cr, uid, ids, part)
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
        
        fsc_pos_id = self.pool.get('account.fiscal.position.rule').search(cr, uid, ['&',('company_id','=', obj_shop.company_id.id),('use_sale','=',True),('fiscal_operation_category_id','=',fiscal_operation_category_id),
                                                                                    '|',('from_country','=',from_country),('from_country','=',False),
                                                                                    '|',('to_country','=',to_country),('to_country','=',False),
                                                                                    '|',('from_state','=',from_state),('from_state','=',False),
                                                                                    '|',('to_state','=',to_state),('to_state','=',False),
                                                                                    '|',('partner_fiscal_type_id','=',partner_fiscal_type),('partner_fiscal_type_id','=',False),
                                                                                    ])
        
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
        
        
        fsc_pos_id = self.pool.get('account.fiscal.position.rule').search(cr, uid, ['&',('company_id','=',obj_shop.company_id.id), ('use_sale','=',True), ('fiscal_operation_category_id','=',fiscal_operation_category_id),
                                                                                    '|',('from_country','=',from_country),('from_country','=',False),
                                                                                    '|',('to_country','=',to_country),('to_country','=',False),
                                                                                    '|',('from_state','=',from_state),('from_state','=',False),
                                                                                    '|',('to_state','=',to_state),('to_state','=',False),
                                                                                    '|',('partner_fiscal_type_id','=',partner_fiscal_type),('partner_fiscal_type_id','=',False),
                                                                                    ])
    
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
            
        fsc_pos_id = self.pool.get('account.fiscal.position.rule').search(cr, uid, ['&',('company_id','=', obj_shop.company_id.id),('use_sale','=',True),('fiscal_operation_category_id','=',fiscal_operation_category_id),
                                                                                    '|',('from_country','=',from_country),('from_country','=',False),
                                                                                    '|',('to_country','=',to_country),('to_country','=',False),
                                                                                    '|',('from_state','=',from_state),('from_state','=',False),
                                                                                    '|',('to_state','=',to_state),('to_state','=',False),
                                                                                    '|',('partner_fiscal_type_id','=',partner_fiscal_type),('partner_fiscal_type_id','=',False),
                                                                                    ])
        
        if fsc_pos_id:
            obj_fpo_rule = self.pool.get('account.fiscal.position.rule').browse(cr, uid, fsc_pos_id)[0]
            result['value']['fiscal_position'] = obj_fpo_rule.fiscal_position_id.id
            result['value']['fiscal_operation_id'] = obj_fpo_rule.fiscal_position_id.fiscal_operation_id.id
        
        return result
    
    def _make_invoice(self, cr, uid, order, lines, context=None):
        journal_obj = self.pool.get('account.journal')
        inv_obj = self.pool.get('account.invoice')
        obj_invoice_line = self.pool.get('account.invoice.line')
        lines_service = []
        lines_product = []
        comment = ''
        
        if order.fiscal_operation_id.inv_copy_note:
           comment = order.fiscal_operation_id.note
        
        if order.note:
            comment += ' - ' + order.note

        if context is None:
            context = {}

        company_id = self.pool.get('res.company').browse(cr, uid,order.company_id.id)
        fiscal_document_serie_ids = [fdoc for fdoc in company_id.document_serie_product_ids if fdoc.fiscal_document_id.id == order.fiscal_operation_id.fiscal_document_id.id]
        
        if not fiscal_document_serie_ids:
            raise osv.except_osv(_('No fiscal document serie found !'),_("No fiscal document serie found for selected company %s, fiscal operation: '%s' and fiscal documento %s") % (order.company_id.name, order.fiscal_operation_id.code, order.fiscal_operation_id.fiscal_document_id.name))

        journal_ids = [jou for jou in order.fiscal_operation_category_id.journal_ids if jou.company_id.id == company_id.id]
        if journal_ids:
            journal_id = journal_ids[0].id
        else:
            raise osv.except_osv(_('Error !'),
                _('There is no sales journal defined for this company in Fiscal Operation Category: "%s" (id:%d)') % (order.company_id.name, order.company_id.id))
        
        a = order.partner_id.property_account_receivable.id
        pay_term = order.payment_term and order.payment_term.id or False
        invoiced_sale_line_ids = self.pool.get('sale.order.line').search(cr, uid, [('order_id', '=', order.id), ('invoiced', '=', True)], context=context)
        from_line_invoice_ids = []
        for invoiced_sale_line_id in self.pool.get('sale.order.line').browse(cr, uid, invoiced_sale_line_ids, context=context):
            for invoice_line_id in invoiced_sale_line_id.invoice_lines:
                if invoice_line_id.invoice_id.id not in from_line_invoice_ids:
                    from_line_invoice_ids.append(invoice_line_id.invoice_id.id)
        for preinv in order.invoice_ids:
            if preinv.state not in ('cancel',) and preinv.id not in from_line_invoice_ids:
                for preline in preinv.invoice_line:
                    inv_line_id = obj_invoice_line.copy(cr, uid, preline.id, {'invoice_id': False, 'price_unit': -preline.price_unit})
                    lines.append(inv_line_id)
        
        
        order_lines = self.pool.get('sale.order.line').search(cr, uid, [('order_id', '=', order.id), ('invoice_lines', 'in', lines)], context=context)
        for order_line in self.pool.get('sale.order.line').browse(cr, uid, order_lines, context=context):
            inv_line_id = [inv_line for inv_line in order_line.invoice_lines if inv_line.id in lines]
            if inv_line_id:
                obj_invoice_line.write(cr, uid, inv_line_id[0].id, {'fiscal_operation_category_id': order_line.fiscal_operation_category_id.id or order.fiscal_operation_category_id.id, 
                                                                    'fiscal_operation_id': order_line.fiscal_operation_id.id or order.fiscal_operation_id.id, 
                                                                    'cfop_id': (order_line.fiscal_operation_id and order_line.fiscal_operation_id.cfop_id.id) or (order.fiscal_operation_id and order.fiscal_operation_id.cfop_id.id)})   
            
        for inv_line in obj_invoice_line.browse(cr, uid, lines, context=context):
            if inv_line.product_id.fiscal_type == 'service':
                lines_service.append(inv_line.id)
                
            if inv_line.product_id.fiscal_type == 'product': 
                lines_product.append(inv_line.id)
           
        inv = {
            'name': order.client_order_ref or '',
            'origin': order.name,
            'type': 'out_invoice',
            'reference': order.client_order_ref or order.name,
            'account_id': a,
            'partner_id': order.partner_id.id,
            'journal_id': journal_id,
            'address_invoice_id': order.partner_invoice_id.id,
            'address_contact_id': order.partner_order_id.id,
            'invoice_line': [(6, 0, lines)],
            'currency_id': order.pricelist_id.currency_id.id,
            'comment': order.note,
            'payment_term': pay_term,
            'fiscal_position': order.fiscal_position.id or order.partner_id.property_account_position.id,
            'date_invoice': context.get('date_invoice',False),
            'company_id': order.company_id.id,
            'user_id': order.user_id and order.user_id.id or False,
            #l10n_br
            'fiscal_operation_category_id': order.fiscal_operation_category_id.id, 
            'fiscal_operation_id': order.fiscal_operation_id.id, 
            'cfop_id': order.fiscal_operation_id.cfop_id and order.fiscal_operation_id.cfop_id.id, 
            'fiscal_document_id': order.fiscal_operation_id.fiscal_document_id.id, 
            'document_serie_id': fiscal_document_serie_ids[0].id,
            'comment': comment,
        }
        inv.update(self._inv_get(cr, uid, order))
        inv_id = inv_obj.create(cr, uid, inv, context=context)
        data = inv_obj.onchange_payment_term_date_invoice(cr, uid, [inv_id], pay_term, time.strftime('%Y-%m-%d'))
        if data.get('value', False):
            inv_obj.write(cr, uid, [inv_id], data['value'], context=context)
        inv_obj.button_compute(cr, uid, [inv_id])
        return inv_id
    
    def action_ship_create(self, cr, uid, ids, *args):

        result = super(sale_order, self).action_ship_create(cr, uid, ids, *args)

        for order in self.browse(cr, uid, ids, context={}):
            for picking in order.picking_ids:
                self.pool.get('stock.picking').write(cr, uid, picking.id, {'fiscal_operation_category_id': order.fiscal_operation_category_id.id, 'fiscal_operation_id': order.fiscal_operation_id.id, 'fiscal_position': order.fiscal_position.id})

        return result

    def _amount_line_tax(self, cr, uid, line, context=None):
        val = 0.0
        for c in self.pool.get('account.tax').compute_all(cr, uid, line.tax_id, line.price_unit * (1-(line.discount or 0.0)/100.0), line.product_uom_qty, line.order_id.partner_invoice_id.id, line.product_id, line.order_id.partner_id)['taxes']:
            tax_brw = self.pool.get('account.tax').browse(cr, uid, c['id'])
            if not tax_brw.tax_code_id.tax_discount:
                val += c.get('amount', 0.0)
        return val

    def _get_order(self, cr, uid, ids, context={}):
        result = super(sale_order, self)._get_order(cr, uid, ids, context)
        return result.keys()

    def _invoiced_rate(self, cursor, user, ids, name, arg, context=None):
        res = {}
        for sale in self.browse(cursor, user, ids, context=context):
            if sale.invoiced:
                res[sale.id] = 100.0
                continue
            tot = 0.0
            for invoice in sale.invoice_ids:
                if invoice.state not in ('draft', 'cancel') and invoice.fiscal_operation_id.id == sale.fiscal_operation_id.id:
                    tot += invoice.amount_untaxed - invoice.residual
            if tot:
                res[sale.id] = min(100.0, tot * 100.0 / (sale.amount_untaxed or 1.00))
            else:
                res[sale.id] = 0.0
        return res

    _columns = {
                'fiscal_operation_category_id': fields.many2one('l10n_br_account.fiscal.operation.category', 'Categoria', domain="[('type','=','output'),('use_sale','=',True)]" ),
                'fiscal_operation_id': fields.many2one('l10n_br_account.fiscal.operation', 'Operação Fiscal', domain="[('fiscal_operation_category_id','=',fiscal_operation_category_id),('type','=','output'),('use_sale','=',True)]" ),
                'invoiced_rate': fields.function(_invoiced_rate, method=True, string='Invoiced', type='float'),
               }
    
sale_order()

##############################################################################
# Linha da Ordem de Venda Customizada
##############################################################################
class sale_order_line(osv.osv):
    
    _inherit = 'sale.order.line'
    
    _columns = {
                'fiscal_operation_category_id': fields.many2one('l10n_br_account.fiscal.operation.category', 'Categoria', domain="[('type','=','output'),('use_sale','=',True)]", readonly=True, states={'draft':[('readonly',False)]}),
                'fiscal_operation_id': fields.many2one('l10n_br_account.fiscal.operation', 'Operação Fiscal', domain="[('fiscal_operation_category_id','=',fiscal_operation_category_id),('type','=','output'),('use_sale','=',True)]", readonly=True, states={'draft':[('readonly',False)]}),
                'fiscal_position': fields.many2one('account.fiscal.position', 'Fiscal Position', readonly=True, domain="[('fiscal_operation_id','=',fiscal_operation_id)]", states={'draft':[('readonly',False)]}),
                }

    def product_id_change(self, cr, uid, ids, pricelist, product, qty=0,
            uom=False, qty_uos=0, uos=False, name='', partner_id=False,
            lang=False, update_tax=True, date_order=False, packaging=False, fiscal_position=False, flag=False, fiscal_operation_category_id=False, fiscal_operation_id=False, shop_id=False, parent_fiscal_position=False):

        result = super(sale_order_line, self).product_id_change(cr, uid, ids, pricelist, product, qty,
            uom, qty_uos, uos, name, partner_id, lang, update_tax, date_order, packaging, fiscal_position, flag)

        if not fiscal_operation_category_id:
            return result

        default_product_category = self.pool.get('l10n_br_account.product.operation.category').search(cr, uid, [('product_id','=', product),('fiscal_operation_category_source_id','=',fiscal_operation_category_id)])

        if not default_product_category:
            if fiscal_operation_category_id:
                result['value']['fiscal_operation_category_id'] = fiscal_operation_category_id
            
            if fiscal_operation_id:
                result['value']['fiscal_operation_id'] = fiscal_operation_id
            
            #if fiscal_position:
            #    result['value']['fiscal_position'] = fiscal_position
            
            return result

        obj_default_prod_categ = self.pool.get('l10n_br_account.product.operation.category').browse(cr, uid, default_product_category)[0]
        result['value']['fiscal_operation_category_id'] = obj_default_prod_categ.fiscal_operation_category_destination_id.id
        result['value']['fiscal_operation_id'] = False
        
        #Dados do Parceiro
        obj_partner = self.pool.get('res.partner').browse(cr, uid, partner_id)
        partner_addr = self.pool.get('res.partner').address_get(cr, uid, [obj_partner.id], ['default'])
        partner_fiscal_type = obj_partner.partner_fiscal_type_id.id
        partner_addr_default = self.pool.get('res.partner.address').browse(cr, uid, [partner_addr['default']])[0]
        to_country = partner_addr_default.country_id.id
        to_state = partner_addr_default.state_id.id

        #Dados da Empresa
        obj_shop = self.pool.get('sale.shop').browse(cr, uid, shop_id)
        company_addr = self.pool.get('res.partner').address_get(cr, uid, [obj_shop.company_id.partner_id.id], ['default'])
        company_addr_default = self.pool.get('res.partner.address').browse(cr, uid, [company_addr['default']])[0]
        from_country = company_addr_default.country_id.id
        from_state = company_addr_default.state_id.id
        
        fsc_pos_id = self.pool.get('account.fiscal.position.rule').search(cr, uid, ['&',('company_id','=', obj_shop.company_id.id), ('fiscal_operation_category_id','=',obj_default_prod_categ.fiscal_operation_category_destination_id.id), ('use_sale','=',True),
                                                                                    '|',('from_country','=',from_country),('from_country','=',False),
                                                                                    '|',('to_country','=',to_country),('to_country','=',False),
                                                                                    '|',('from_state','=',from_state),('from_state','=',False),
                                                                                    '|',('to_state','=',to_state),('to_state','=',False),
                                                                                    '|',('partner_fiscal_type_id','=',partner_fiscal_type),('partner_fiscal_type_id','=',False),
                                                                                    ])
                                                                                    
                                                                                        
                                                                                            
        if fsc_pos_id:
            obj_fpo_rule = self.pool.get('account.fiscal.position.rule').browse(cr, uid, fsc_pos_id)[0]
            #if fiscal_position != obj_fpo_rule.fiscal_position_id.id:
            #    result['tax_id'] = self.pool.get('account.fiscal.position').map_tax(cr, uid, obj_fpo_rule.fiscal_position_id.id, product_obj.taxes_id)
            #    result['value']['fiscal_position'] = obj_fpo_rule.fiscal_position_id.id
            result['value']['fiscal_operation_id'] = obj_fpo_rule.fiscal_position_id.fiscal_operation_id.id
            
        return result

    def create_sale_order_line_invoice(self, cr, uid, ids, context=None):
        result = super(sale_order_line, self).create_sale_order_line_invoice(cr, uid, ids, context)
        inv_ids = []
        if result:

            for so_line in self.browse(cr, uid, ids):
                for inv_line in so_line.invoice_lines:
                    if inv_line.invoice_id.state in ('draft'):
                        company_id = self.pool.get('res.company').browse(cr, uid,order.company_id.id)
                        if not company_id.document_serie_product_ids:
                            raise osv.except_osv(_('No fiscal document serie found !'),_("No fiscal document serie found for selected company %s and fiscal operation: '%s'") % (order.company_id.name, order.fiscal_operation_id.code))
                        if inv_line.invoice_id.id not in inv_ids: 
                            inv_ids.append(inv_line.id)
                            self.pool.get('account.invoice').write(cr, uid, inv_line.invoice_id.id, {'fiscal_operation_category_id': so_line.order_id.fiscal_operation_category_id.id,
                                                                                                     'fiscal_operation_id': so_line.order_id.fiscal_operation_id.id, 
                                                                                                     'cfop_id': so_line.order_id.fiscal_operation_id.cfop_id.id, 
                                                                                                     'fiscal_document_id': so_line.order_id.fiscal_operation_id.fiscal_document_id.id,
                                                                                                     'document_serie_id': company_id.document_serie_product_ids[0].id})
                        
                        self.pool.get('account.invoice.line').write(cr, uid, inv_line.id, {'cfop_id': so_line.fiscal_operation_id.cfop_id.id, 
                                                                                           'fiscal_operation_category_id': so_line.fiscal_operation_category_id.id, 
                                                                                           'fiscal_operation_id': so_line.fiscal_operation_id.id})

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
