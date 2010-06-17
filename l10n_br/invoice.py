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
from osv import fields, osv
import pooler
from tools import config
from tools.translate import _

##############################################################################
# Fatura (Nota Fiscal) Personalizado
##############################################################################
class account_invoice(osv.osv):
    _inherit = 'account.invoice'

    def _amount_all(self, cr, uid, ids, name, args, context=None):
        
        result = super(account_invoice, self)._amount_all(cr,uid,ids,name,args,context)
        cur_obj = self.pool.get('res.currency')
        tax_obj = self.pool.get('account.tax')
        
        for inv in self.browse(cr,uid,ids, context=context): 
            cur = inv.currency_id
            company_currency = inv.company_id.currency_id.id
            for line in inv.invoice_line:
                for tax in tax_obj.compute(cr, uid, line.invoice_line_tax_id, (line.price_unit* (1-(line.discount or 0.0)/100.0)), line.quantity, inv.address_invoice_id.id, line.product_id, inv.partner_id):
                    obj_current_tax = self.pool.get('account.tax').browse(cr, uid, [tax['id']])[0]
                    if obj_current_tax.price_include:
                        result[inv.id]['amount_tax'] -= cur_obj.compute(cr, uid, inv.currency_id.id, company_currency, tax['amount'] * tax['tax_sign'], context={'date': inv.date_invoice or time.strftime('%Y-%m-%d')}, round=False)
            result[inv.id]['amount_total'] = result[inv.id]['amount_tax'] + result[inv.id]['amount_untaxed']
        return result
    
    def _get_invoice_line(self, cr, uid, ids, context=None):
        result = super(account_invoice, self)._get_invoice_line(cr, uid, ids, context)
        return result.keys()

    def _get_invoice_tax(self, cr, uid, ids, context=None):
        result = super(account_invoice, self)._get_invoice_tax(cr, uid, ids, context)
        return result.keys()

    _columns = {
        'state_nfe': fields.selection([
            ('signed','Assinada'),
            ('authorized','Autorizada'),
            ('canceled','Cancelada'),
            ('denied','Denegada'),
            ('typing','Em Digitação'),
            ('processing','Em processamento na SEFAZ'),
            ('rejected','Rejeitada'),
            ('pending','Transmitida com Pendência'),
            ('validated','Validada')
            ],'Status NFe', select=True, readonly=True),
        'access_key_nfe': fields.char('Chave de Acesso', size=44),
        'fiscal_document_id': fields.many2one('l10n_br.fiscal.document', 'Documento'),
        'fiscal_operation_category_id': fields.many2one('l10n_br.fiscal.operation.category', 'Categoria', requeried=True),
        'fiscal_operation_id': fields.many2one('l10n_br.fiscal.operation', 'Operação Fiscal'),
        'cfop_id': fields.many2one('l10n_br.cfop', 'CFOP'),
        'amount_untaxed': fields.function(_amount_all, method=True, digits=(16, int(config['price_accuracy'])),string='Untaxed',
            store={
                'account.invoice': (lambda self, cr, uid, ids, c={}: ids, ['invoice_line'], 20),
                'account.invoice.tax': (_get_invoice_tax, None, 20),
                'account.invoice.line': (_get_invoice_line, ['price_unit','invoice_line_tax_id','quantity','discount'], 20),
            },
            multi='all'),
        'amount_tax': fields.function(_amount_all, method=True, digits=(16, int(config['price_accuracy'])), string='Tax',
            store={
                'account.invoice': (lambda self, cr, uid, ids, c={}: ids, ['invoice_line'], 20),
                'account.invoice.tax': (_get_invoice_tax, None, 20),
                'account.invoice.line': (_get_invoice_line, ['price_unit','invoice_line_tax_id','quantity','discount'], 20),
            },
            multi='all'),
        'amount_total': fields.function(_amount_all, method=True, digits=(16, int(config['price_accuracy'])), string='Total',
            store={
                'account.invoice': (lambda self, cr, uid, ids, c={}: ids, ['invoice_line'], 20),
                'account.invoice.tax': (_get_invoice_tax, None, 20),
                'account.invoice.line': (_get_invoice_line, ['price_unit','invoice_line_tax_id','quantity','discount'], 20),
            },
            multi='all'),
    }

    def onchange_partner_id(self, cr, uid, ids, type, partner_id,
            date_invoice=False, payment_term=False,company_id=False, partner_bank_id=False ):

        result = super(account_invoice, self).onchange_partner_id(cr,uid,ids,type,partner_id,date_invoice,payment_term,partner_bank_id)
        result['value']['fiscal_operation_id'] = False
        result['value']['cfop_id'] = False
        result['value']['fiscal_document_id'] = False
        
        if not partner_id or not company_id:
            return result

        obj_company = self.pool.get('res.company').browse(cr, uid, [company_id])[0]

        company_addr = self.pool.get('res.partner').address_get(cr, uid, [obj_company.partner_id.id], ['default'])
        company_addr_default = self.pool.get('res.partner.address').browse(cr, uid, [company_addr['default']])[0]

        from_country = company_addr_default.country_id.id
        from_state = company_addr_default.state_id.id

        if result['value']['address_invoice_id']:
            ptn_invoice_id = result['value']['address_invoice_id']

        obj_partner = self.pool.get('res.partner').browse(cr, uid, [partner_id])[0]
        partner_fiscal_type = obj_partner.partner_fiscal_type_id.id
        
        if obj_partner.property_account_position.id:
            obj_fpo = self.pool.get('account.fiscal.position').browse(cr, uid, [obj_fpo_rule.fiscal_position_id.id])[0]
            obj_foperation = self.pool.get('l10n_br.fiscal.operation').browse(cr, uid, [obj_fpo.fiscal_operation_id.id])[0]
            result['value']['fiscal_position'] = obj_fpo.id
            result['value']['fiscal_operation_id'] = obj_foperation.id
            result['value']['cfop_id'] = obj_foperation.cfop_id.id
            result['value']['fiscal_document_id'] = obj_foperation.fiscal_document_id.id

            for inv in self.browse(cr,uid,ids): 
                for line in inv.invoice_line:
                    line.cfop_id = obj_foperation.cfop_id.id
                    
            return result
        
        partner_addr_default = self.pool.get('res.partner.address').browse(cr, uid, [ptn_invoice_id])[0]

        to_country = partner_addr_default.country_id.id
        to_state = partner_addr_default.state_id.id

        fsc_pos_id = self.pool.get('account.fiscal.position.rule').search(cr, uid, [('company_id','=',company_id), ('from_country','=',from_country),('from_state','=',from_state),('to_country','=',to_country),('to_state','=',to_state),('use_invoice','=',True),('partner_fiscal_type_id','=',partner_fiscal_type)])
        
        if fsc_pos_id:
            obj_fpo_rule = self.pool.get('account.fiscal.position.rule').browse(cr, uid, fsc_pos_id)[0]
            obj_fpo = self.pool.get('account.fiscal.position').browse(cr, uid, [obj_fpo_rule.fiscal_position_id.id])[0]
            obj_foperation = self.pool.get('l10n_br.fiscal.operation').browse(cr, uid, [obj_fpo.fiscal_operation_id.id])[0]
            result['value']['fiscal_position'] = obj_fpo.id
            result['value']['fiscal_operation_id'] = obj_foperation.id
            result['value']['cfop_id'] = obj_foperation.cfop_id.id
            result['value']['fiscal_document_id'] = obj_foperation.fiscal_document_id.id
            
            for inv in self.browse(cr,uid,ids):
                for line in inv.invoice_line:
                    line.cfop_id = obj_foperation.cfop_id.id
                    #line.write(cr, uid, line.id, {'cfop_id': obj_foperation.cfop_id.id})
        return result
    
    def onchange_company_id(self, cr, uid, ids, cpy_id, ptn_id, ptn_invoice_id):
        
        result = super(account_invoice, self).onchange_company_id(cr,uid,ids,cpy_id,ptn_id,ptn_invoice_id)
        result['value']['fiscal_operation_id'] = False
        result['value']['cfop_id'] = False
        result['value']['fiscal_document_id'] = False
        
        if not ptn_id or not cpy_id or not ptn_invoice_id:
            return result
        
        obj_company = self.pool.get('res.company').browse(cr, uid, [cpy_id])[0]
        
        company_addr = self.pool.get('res.partner').address_get(cr, uid, [obj_company.partner_id.id], ['default'])
        company_addr_default = self.pool.get('res.partner.address').browse(cr, uid, [company_addr['default']])[0]
        
        from_country = company_addr_default.country_id.id
        from_state = company_addr_default.state_id.id

        obj_partner = self.pool.get('res.partner').browse(cr, uid, [ptn_id])[0]
        partner_fiscal_type = obj_partner.partner_fiscal_type_id.id
        
        if obj_partner.property_account_position.id:
            obj_fpo = self.pool.get('account.fiscal.position').browse(cr, uid, [obj_fpo_rule.fiscal_position_id.id])[0]
            obj_foperation = self.pool.get('l10n_br.fiscal.operation').browse(cr, uid, [obj_fpo.fiscal_operation_id.id])[0]
            result['value']['fiscal_position'] = obj_fpo.id
            result['value']['fiscal_operation_id'] = obj_foperation.id
            result['value']['cfop_id'] = obj_foperation.cfop_id.id
            result['value']['fiscal_document_id'] = obj_foperation.fiscal_document_id.id
            return result
        
        partner_addr_invoice = self.pool.get('res.partner.address').browse(cr, uid, [ptn_invoice_id])[0]

        to_country = partner_addr_invoice.country_id.id
        to_state = partner_addr_invoice.state_id.id

        fsc_pos_id = self.pool.get('account.fiscal.position.rule').search(cr, uid, [('company_id','=',cpy_id), ('from_country','=',from_country),('from_state','=',from_state),('to_country','=',to_country),('to_state','=',to_state),('use_invoice','=',True),('partner_fiscal_type_id','=',partner_fiscal_type)])
        
        if fsc_pos_id: 
            obj_fpo_rule = self.pool.get('account.fiscal.position.rule').browse(cr, uid, fsc_pos_id)[0]
            obj_fpo = self.pool.get('account.fiscal.position').browse(cr, uid, [obj_fpo_rule.fiscal_position_id.id])[0]
            obj_foperation = self.pool.get('l10n_br.fiscal.operation').browse(cr, uid, [obj_fpo.fiscal_operation_id.id])[0]
            result['value']['fiscal_position'] = obj_fpo.id
            result['value']['fiscal_operation_id'] = obj_foperation.id
            result['value']['cfop_id'] = obj_foperation.cfop_id.id
            result['value']['fiscal_document_id'] = obj_foperation.fiscal_document_id.id
       
            for inv in self.browse(cr,uid,ids): 
                for line in inv.invoice_line:
                    line.cfop_id = obj_foperation.cfop_id.id
                    
        return result    

    def onchange_address_invoice_id(self, cr, uid, ids, cpy_id, ptn_id, ptn_invoice_id):
        
        result = super(account_invoice, self).onchange_address_invoice_id(cr,uid,ids,cpy_id,ptn_id,ptn_invoice_id)
        result['value']['fiscal_operation_id'] = False
        result['value']['cfop_id'] = False
        result['value']['fiscal_document_id'] = False
        
        if not ptn_id or not cpy_id or not ptn_invoice_id:
            return result
        
        obj_company = self.pool.get('res.company').browse(cr, uid, [cpy_id])[0]
        
        company_addr = self.pool.get('res.partner').address_get(cr, uid, [obj_company.partner_id.id], ['default'])
        company_addr_default = self.pool.get('res.partner.address').browse(cr, uid, [company_addr['default']])[0]
        
        from_country = company_addr_default.country_id.id
        from_state = company_addr_default.state_id.id

        obj_partner = self.pool.get('res.partner').browse(cr, uid, [ptn_id])[0]
        partner_fiscal_type = obj_partner.partner_fiscal_type_id.id
        
        if obj_partner.property_account_position.id:
            obj_fpo = self.pool.get('account.fiscal.position').browse(cr, uid, [obj_fpo_rule.fiscal_position_id.id])[0]
            obj_foperation = self.pool.get('l10n_br.fiscal.operation').browse(cr, uid, [obj_fpo.fiscal_operation_id.id])[0]
            result['value']['fiscal_position'] = obj_fpo.id
            result['value']['fiscal_operation_id'] = obj_foperation.id
            result['value']['cfop_id'] = obj_foperation.cfop_id.id
            result['value']['fiscal_document_id'] = obj_foperation.fiscal_document_id.id
            return result

        partner_addr_invoice = self.pool.get('res.partner.address').browse(cr, uid, [ptn_invoice_id])[0]

        to_country = partner_addr_invoice.country_id.id
        to_state = partner_addr_invoice.state_id.id

        fsc_pos_id = self.pool.get('account.fiscal.position.rule').search(cr, uid, [('company_id','=', cpy_id), ('from_country','=',from_country),('from_state','=',from_state),('to_country','=',to_country),('to_state','=',to_state),('use_invoice','=',True)])
        
        if fsc_pos_id:
            obj_fpo_rule = self.pool.get('account.fiscal.position.rule').browse(cr, uid, fsc_pos_id)[0]
            obj_fpo = self.pool.get('account.fiscal.position').browse(cr, uid, [obj_fpo_rule.fiscal_position_id.id])[0]
            obj_foperation = self.pool.get('l10n_br.fiscal.operation').browse(cr, uid, [obj_fpo.fiscal_operation_id.id])[0]
            result['value']['fiscal_position'] = obj_fpo.id
            result['value']['fiscal_operation_id'] = obj_foperation.id
            result['value']['cfop_id'] = obj_foperation.cfop_id.id
            result['value']['fiscal_document_id'] = obj_foperation.fiscal_document_id.id
            
            for inv in self.browse(cr,uid,ids): 
                for line in inv.invoice_line:
                    line.cfop_id = obj_foperation.cfop_id.id
       
        return result  

    def fiscal_operation_id_change(self, cr, uid, ids, fiscal_operation_id):

        result = {'value': {'cfop_id': False, 'fiscal_document_id': False}}

        if not fiscal_operation_id:
            return result

        obj_fiscal_operation = self.pool.get('l10n_br.fiscal.operation').browse(cr, uid, [fiscal_operation_id])[0]

        result['value']['cfop_id'] =  obj_fiscal_operation.cfop_id.id
        result['value']['fiscal_document_id'] = obj_fiscal_operation.fiscal_document_id.id

        return result
    
    def fiscal_position_id_change(self, cr, uid, ids, fiscal_position_id):

        result = {'value': {'cfop_id': False, 'fiscal_document_id': False,'fiscal_position': False, 'fiscal_operation_id': False }}

        if not fiscal_position_id:
            return result

        obj_fiscal_position = self.pool.get('account.fiscal.position').browse(cr, uid, [fiscal_position_id])[0]
        obj_fiscal_operation = self.pool.get('l10n_br.fiscal.operation').browse(cr, uid, [obj_fiscal_position.fiscal_operation_id.id])[0]

        result['value']['cfop_id'] =  obj_fiscal_operation.cfop_id.id
        result['value']['fiscal_operation_id'] = obj_fiscal_operation.id
        result['value']['fiscal_document_id'] = obj_fiscal_operation.fiscal_document_id.id
        result['value']['fiscal_position'] = fiscal_position_id

        return result

account_invoice()

class account_invoice_line(osv.osv):
    _inherit = 'account.invoice.line'
    _columns = {
                'cfop_id': fields.many2one('l10n_br.cfop', 'CFOP'),
                }

    def product_id_change(self, cr, uid, ids, product, uom, qty=0, name='', type='out_invoice', partner_id=False, fposition_id=False, price_unit=False, address_invoice_id=False, context=None, cfop_id=False):

        result = super(account_invoice_line, self).product_id_change(cr, uid, ids, product, uom, qty, name, type, partner_id, fposition_id, price_unit, address_invoice_id, context)
        
        if not cfop_id:
            return result

        result['value']['cfop_id'] =  cfop_id

        return result

account_invoice_line()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: