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
import decimal_precision as dp
import pooler
from tools import config
from tools.translate import _

##############################################################################
# Fatura (Nota Fiscal) Personalizado
##############################################################################
class account_invoice(osv.osv):
    _inherit = 'account.invoice'

    def _amount_all(self, cr, uid, ids, name, args, context=None):
        res = {}
        for invoice in self.browse(cr, uid, ids, context=context):
            res[invoice.id] = {
                'amount_untaxed': 0.0,
                'amount_tax': 0.0,
                'amount_tax_discount': 0.0,
                'amount_total': 0.0,
                'icms_base': 0.0,
                'icms_value': 0.0,
                'ipi_base': 0.0,
                'ipi_value': 0.0,
            }
            for line in invoice.invoice_line:
                res[invoice.id]['amount_untaxed'] += line.price_total
                res[invoice.id]['amount_tax_discount'] += line.price_total - line.price_subtotal
                res[invoice.id]['icms_base'] += line.icms_base
                res[invoice.id]['icms_value'] += line.icms_value
                res[invoice.id]['ipi_base'] += line.ipi_base
                res[invoice.id]['ipi_value'] += line.ipi_value
                
               
            for invoice_tax in invoice.tax_line:
                    res[invoice.id]['amount_tax'] += invoice_tax.amount
            
            if res[invoice.id]['amount_tax_discount'] > 0 and res[invoice.id]['amount_tax'] > 0:
                res[invoice.id]['amount_tax'] = res[invoice.id]['amount_tax'] - res[invoice.id]['amount_tax_discount']
                
            res[invoice.id]['amount_total'] = res[invoice.id]['amount_tax'] + res[invoice.id]['amount_untaxed']
            
        return res

    def _get_invoice_line(self, cr, uid, ids, context=None):
        result = super(account_invoice, self)._get_invoice_line(cr, uid, ids, context)
        return result.keys()

    def _get_invoice_tax(self, cr, uid, ids, context=None):
        result = super(account_invoice, self)._get_invoice_tax(cr, uid, ids, context)
        return result.keys()

    _columns = {
        'state': fields.selection([
            ('draft','Draft'),
            ('proforma','Pro-forma'),
            ('proforma2','Pro-forma'),
            ('open','Open'),
            ('sefaz_out','Enviar para Receita'),
            ('sefaz_aut','Autorizada pela Receita'),
            ('paid','Paid'),
            ('cancel','Cancelled')
            ],'State', select=True, readonly=True,
            help=' * The \'Draft\' state is used when a user is encoding a new and unconfirmed Invoice. \
            \n* The \'Pro-forma\' when invoice is in Pro-forma state,invoice does not have an invoice number. \
            \n* The \'Open\' state is used when user create invoice,a invoice number is generated.Its in open state till user does not pay invoice. \
            \n* The \'Paid\' state is set automatically when invoice is paid.\
            \n* The \'sefaz_out\' Gerado aquivo de exportação para sistema daReceita.\
            \n* The \'sefaz_aut\' Recebido arquivo de autolização da Receita.\
            \n* The \'Cancelled\' state is used when user cancel invoice.'),
        'access_key_nfe': fields.char('Chave de Acesso', size=44, readonly=True, states={'draft':[('readonly',False)]}),
        'fiscal_document_id': fields.many2one('l10n_br_account.fiscal.document', 'Documento',  readonly=True, states={'draft':[('readonly',False)]}),
        'document_serie_id': fields.many2one('l10n_br_account.document.serie', 'Serie', domain="[('fiscal_document_id','=',fiscal_document_id)]", readonly=True, states={'draft':[('readonly',False)]}),
        'fiscal_operation_category_id': fields.many2one('l10n_br_account.fiscal.operation.category', 'Categoria', readonly=True, states={'draft':[('readonly',False)]}),
        'fiscal_operation_id': fields.many2one('l10n_br_account.fiscal.operation', 'Operação Fiscal', domain="[('fiscal_operation_category_id','=',fiscal_operation_category_id)]", readonly=True, states={'draft':[('readonly',False)]}),
        'cfop_id': fields.many2one('l10n_br_account.cfop', 'CFOP', readonly=True, states={'draft':[('readonly',False)]}),
        'amount_untaxed': fields.function(_amount_all, method=True, digits_compute=dp.get_precision('Account'), string='Untaxed',
            store={
                'account.invoice': (lambda self, cr, uid, ids, c={}: ids, ['invoice_line'], 20),
                'account.invoice.tax': (_get_invoice_tax, None, 20),
                'account.invoice.line': (_get_invoice_line, ['price_unit','invoice_line_tax_id','quantity','discount'], 20),
            },
            multi='all'),
        'amount_tax': fields.function(_amount_all, method=True, digits_compute=dp.get_precision('Account'), string='Tax',
            store={
                'account.invoice': (lambda self, cr, uid, ids, c={}: ids, ['invoice_line'], 20),
                'account.invoice.tax': (_get_invoice_tax, None, 20),
                'account.invoice.line': (_get_invoice_line, ['price_unit','invoice_line_tax_id','quantity','discount'], 20),
            },
            multi='all'),
        'amount_total': fields.function(_amount_all, method=True, digits_compute=dp.get_precision('Account'), string='Total',
            store={
                'account.invoice': (lambda self, cr, uid, ids, c={}: ids, ['invoice_line'], 20),
                'account.invoice.tax': (_get_invoice_tax, None, 20),
                'account.invoice.line': (_get_invoice_line, ['price_unit','invoice_line_tax_id','quantity','discount'], 20),
            },
            multi='all'),
        'icms_base': fields.function(_amount_all, method=True, digits_compute=dp.get_precision('Account'), string='Base ICMS',
            store={
                'account.invoice': (lambda self, cr, uid, ids, c={}: ids, ['invoice_line'], 20),
                #'account.invoice.tax': (_get_invoice_tax, None, 20),
                #'account.invoice.line': (_get_invoice_line, ['price_unit','invoice_line_tax_id','quantity','discount'], 20),
            },
            multi='all'),
        'icms_value': fields.function(_amount_all, method=True, digits_compute=dp.get_precision('Account'), string='Valor ICMS',
            store={
                'account.invoice': (lambda self, cr, uid, ids, c={}: ids, ['invoice_line'], 20),
        #        'account.invoice.tax': (_get_invoice_tax, None, 20),
        #        'account.invoice.line': (_get_invoice_line, ['price_unit','invoice_line_tax_id','quantity','discount'], 20),
            },
            multi='all'),
        'ipi_base': fields.function(_amount_all, method=True, digits_compute=dp.get_precision('Account'), string='Base IPI',
            store={
                'account.invoice': (lambda self, cr, uid, ids, c={}: ids, ['invoice_line'], 20),
         #       'account.invoice.tax': (_get_invoice_tax, None, 20),
         #       'account.invoice.line': (_get_invoice_line, ['price_unit','invoice_line_tax_id','quantity','discount'], 20),
            },
            multi='all'),
        'ipi_value': fields.function(_amount_all, method=True, digits_compute=dp.get_precision('Account'), string='Valor IPI',
            store={
                'account.invoice': (lambda self, cr, uid, ids, c={}: ids, ['invoice_line'], 20),
        #        'account.invoice.tax': (_get_invoice_tax, None, 20),
        #        'account.invoice.line': (_get_invoice_line, ['price_unit','invoice_line_tax_id','quantity','discount'], 20),
            },
            multi='all'),     
    }

    def onchange_partner_id(self, cr, uid, ids, type, partner_id,\
            date_invoice=False, payment_term=False, partner_bank_id=False, company_id=False, fiscal_operation_category_id=False):

        result = super(account_invoice, self).onchange_partner_id(cr, uid, ids, type, partner_id, date_invoice, payment_term, partner_bank_id, company_id)
        result['value']['fiscal_operation_id'] = False
        result['value']['cfop_id'] = False
        result['value']['fiscal_document_id'] = False
        
        if not partner_id or not company_id or not result['value']['address_invoice_id']:
            return result

        obj_company = self.pool.get('res.company').browse(cr, uid, [company_id])[0]

        company_addr = self.pool.get('res.partner').address_get(cr, uid, [obj_company.partner_id.id], ['default'])
        company_addr_default = self.pool.get('res.partner.address').browse(cr, uid, [company_addr['default']])[0]

        from_country = company_addr_default.country_id.id
        from_state = company_addr_default.state_id.id

        obj_partner = self.pool.get('res.partner').browse(cr, uid, [partner_id])[0]
        partner_fiscal_type = obj_partner.partner_fiscal_type_id.id
        
        #if obj_partner.property_account_position.id:
        #    obj_fpo = self.pool.get('account.fiscal.position').browse(cr, uid, [obj_fpo_rule.fiscal_position_id.id])[0]
        #    obj_foperation = self.pool.get('l10n_br.fiscal.operation').browse(cr, uid, [obj_fpo.fiscal_operation_id.id])[0]
        #    result['value']['fiscal_position'] = obj_fpo.id
        #    result['value']['fiscal_operation_id'] = obj_foperation.id
        #    result['value']['cfop_id'] = obj_foperation.cfop_id.id
        #    result['value']['fiscal_document_id'] = obj_foperation.fiscal_document_id.id

        #    for inv in self.browse(cr,uid,ids): 
        #        for line in inv.invoice_line:
        #            line.cfop_id = obj_foperation.cfop_id.id
        #            
        #    return result
        
        partner_addr_default = self.pool.get('res.partner.address').browse(cr, uid, [result['value']['address_invoice_id']])[0]

        to_country = partner_addr_default.country_id.id
        to_state = partner_addr_default.state_id.id

        fsc_pos_id = self.pool.get('account.fiscal.position.rule').search(cr, uid, [('company_id','=',company_id), ('from_country','=',from_country),('from_state','=',from_state),('to_country','=',to_country),('to_state','=',to_state),('use_invoice','=',True),('partner_fiscal_type_id','=',partner_fiscal_type),('fiscal_operation_category_id','=',fiscal_operation_category_id)])
        
        if fsc_pos_id:
            obj_fpo_rule = self.pool.get('account.fiscal.position.rule').browse(cr, uid, fsc_pos_id)[0]
            obj_fpo = self.pool.get('account.fiscal.position').browse(cr, uid, [obj_fpo_rule.fiscal_position_id.id])[0]
            obj_foperation = self.pool.get('l10n_br_account.fiscal.operation').browse(cr, uid, [obj_fpo.fiscal_operation_id.id])[0]
            result['value']['fiscal_position'] = obj_fpo.id
            result['value']['fiscal_operation_id'] = obj_foperation.id
            result['value']['cfop_id'] = obj_foperation.cfop_id.id
            result['value']['fiscal_document_id'] = obj_foperation.fiscal_document_id.id
            
            #for inv in self.browse(cr,uid,ids):
            #    for line in inv.invoice_line:
            #        line.cfop_id = obj_foperation.cfop_id.id
                    #line.write(cr, uid, line.id, {'cfop_id': obj_foperation.cfop_id.id})
        return result
    
    def onchange_company_id(self, cr, uid, ids, company_id, partner_id, type, invoice_line, currency_id, address_invoice_id, fiscal_operation_category_id=False):
        
        result = super(account_invoice, self).onchange_company_id(cr, uid, ids, company_id, partner_id, type, invoice_line, currency_id, address_invoice_id)
        result['value']['fiscal_operation_id'] = False
        result['value']['cfop_id'] = False
        result['value']['fiscal_document_id'] = False
        
        if not partner_id or not company_id or not address_invoice_id:
            return result
        
        obj_company = self.pool.get('res.company').browse(cr, uid, [company_id])[0]
        
        company_addr = self.pool.get('res.partner').address_get(cr, uid, [obj_company.partner_id.id], ['default'])
        company_addr_default = self.pool.get('res.partner.address').browse(cr, uid, [company_addr['default']])[0]
        
        from_country = company_addr_default.country_id.id
        from_state = company_addr_default.state_id.id

        obj_partner = self.pool.get('res.partner').browse(cr, uid, [partner_id])[0]
        partner_fiscal_type = obj_partner.partner_fiscal_type_id.id
        
        if obj_partner.property_account_position.id:
            obj_fpo = self.pool.get('account.fiscal.position').browse(cr, uid, [obj_fpo_rule.fiscal_position_id.id])[0]
            obj_foperation = self.pool.get('l10n_br_account.fiscal.operation').browse(cr, uid, [obj_fpo.fiscal_operation_id.id])[0]
            result['value']['fiscal_position'] = obj_fpo.id
            result['value']['fiscal_operation_id'] = obj_foperation.id
            result['value']['cfop_id'] = obj_foperation.cfop_id.id
            result['value']['fiscal_document_id'] = obj_foperation.fiscal_document_id.id
            return result
        
        partner_addr_invoice = self.pool.get('res.partner.address').browse(cr, uid, [address_invoice_id])[0]

        to_country = partner_addr_invoice.country_id.id
        to_state = partner_addr_invoice.state_id.id

        fsc_pos_id = self.pool.get('account.fiscal.position.rule').search(cr, uid, [('company_id','=',company_id), ('from_country','=',from_country),('from_state','=',from_state),('to_country','=',to_country),('to_state','=',to_state),('use_invoice','=',True),('partner_fiscal_type_id','=',partner_fiscal_type),('fiscal_operation_category_id','=',fiscal_operation_category_id)])
        
        if fsc_pos_id: 
            obj_fpo_rule = self.pool.get('account.fiscal.position.rule').browse(cr, uid, fsc_pos_id)[0]
            obj_fpo = self.pool.get('account.fiscal.position').browse(cr, uid, [obj_fpo_rule.fiscal_position_id.id])[0]
            obj_foperation = self.pool.get('l10n_br_account.fiscal.operation').browse(cr, uid, [obj_fpo.fiscal_operation_id.id])[0]
            result['value']['fiscal_position'] = obj_fpo.id
            result['value']['fiscal_operation_id'] = obj_foperation.id
            result['value']['cfop_id'] = obj_foperation.cfop_id.id
            result['value']['fiscal_document_id'] = obj_foperation.fiscal_document_id.id
       
            for inv in self.browse(cr,uid,ids): 
                for line in inv.invoice_line:
                    line.cfop_id = obj_foperation.cfop_id.id
                    
        return result    

    def onchange_address_invoice_id(self, cr, uid, ids, cpy_id, ptn_id, ptn_invoice_id, fiscal_operation_category_id=False):
        
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
            obj_foperation = self.pool.get('l10n_br_account.fiscal.operation').browse(cr, uid, [obj_fpo.fiscal_operation_id.id])[0]
            result['value']['fiscal_position'] = obj_fpo.id
            result['value']['fiscal_operation_id'] = obj_foperation.id
            result['value']['cfop_id'] = obj_foperation.cfop_id.id
            result['value']['fiscal_document_id'] = obj_foperation.fiscal_document_id.id
            return result

        partner_addr_invoice = self.pool.get('res.partner.address').browse(cr, uid, [ptn_invoice_id])[0]

        to_country = partner_addr_invoice.country_id.id
        to_state = partner_addr_invoice.state_id.id

        fsc_pos_id = self.pool.get('account.fiscal.position.rule').search(cr, uid, [('company_id','=', cpy_id), ('from_country','=',from_country),('from_state','=',from_state),('to_country','=',to_country),('to_state','=',to_state),('use_invoice','=',True),('fiscal_operation_category_id','=',fiscal_operation_category_id)])
        
        if fsc_pos_id:
            obj_fpo_rule = self.pool.get('account.fiscal.position.rule').browse(cr, uid, fsc_pos_id)[0]
            obj_fpo = self.pool.get('account.fiscal.position').browse(cr, uid, [obj_fpo_rule.fiscal_position_id.id])[0]
            obj_foperation = self.pool.get('l10n_br_account.fiscal.operation').browse(cr, uid, [obj_fpo.fiscal_operation_id.id])[0]
            result['value']['fiscal_position'] = obj_fpo.id
            result['value']['fiscal_operation_id'] = obj_foperation.id
            result['value']['cfop_id'] = obj_foperation.cfop_id.id
            result['value']['fiscal_document_id'] = obj_foperation.fiscal_document_id.id
            
            for inv in self.browse(cr,uid,ids): 
                for line in inv.invoice_line:
                    line.cfop_id = obj_foperation.cfop_id.id
       
        return result  

    def onchange_cfop_id(self, cr, uid, ids, cfop_id):
    
        if not cfop_id:
            return False
        
        for inv in self.browse(cr, uid, ids):    
            for inv_line in inv.invoice_line:
                self.pool.get('account.invoice.line').write(cr, uid, inv_line.id, {'cfop_id': inv_line.fiscal_operation_id.cfop_id.id})
            
        return {'value': {'cfop_id': cfop_id}}

account_invoice()

class account_invoice_line(osv.osv):
    _inherit = 'account.invoice.line'
    
    def _amount_line(self, cr, uid, ids, prop, unknow_none, unknow_dict):
        
        res = {} #super(account_invoice_line, self)._amount_line(cr, uid, ids, prop, unknow_none, unknow_dict)
        
        tax_obj = self.pool.get('account.tax')
        fsc_op_line_obj = self.pool.get('l10n_br_account.fiscal.operation.line')
        cur_obj = self.pool.get('res.currency')
        
        for line in self.browse(cr, uid, ids):
            res[line.id] = {
                'price_subtotal': 0.0,
                'price_total': 0.0,
                'icms_base': 0.0,
                'icms_value': 0.0,
                'icms_percent': 0.0,
                'icms_cst': '',
                'ipi_base': 0.0,
                'ipi_value': 0.0,
                'ipi_percent': 0.0,
                'ipi_cst': '',
                'pis_base': 0.0,
                'pis_value': 0.0,
                'pis_percent': 0.0,
                'pis_cst': '',
                'cofins_base': 0.0,
                'cofins_value': 0.0,
                'cofins_percent': 0.0,
                'cofins_cst': '',
            }
            price = line.price_unit * (1-(line.discount or 0.0)/100.0)
            taxes = tax_obj.compute_all(cr, uid, line.invoice_line_tax_id, price, line.quantity, product=line.product_id, address_id=line.invoice_id.address_invoice_id, partner=line.invoice_id.partner_id)
            
            icms_base = 0.0
            icms_value = 0.0
            icms_percent = 0.0
            icms_cst = ''
            ipi_base = 0.0
            ipi_value = 0.0
            ipi_percent = 0.0
            ipi_cst = ''
            pis_base = 0.0
            pis_value = 0.0
            pis_percent = 0.0
            pis_cst = ''
            cofins_base = 0.0
            cofins_value = 0.0
            cofins_percent = 0.0
            cofins_cst = ''
            
            for tax in taxes['taxes']:
                fsc_op_line_ids = 0
                tax_brw = tax_obj.browse(cr, uid, tax['id'])
                if line.invoice_id.fiscal_operation_id:
                    fsc_op_line_ids = fsc_op_line_obj.search(cr, uid, [('tax_code_id','=', tax_brw.tax_code_id.id),('fiscal_operation_id','=',line.invoice_id.fiscal_operation_id.id)])
                cst_code = ''
                if fsc_op_line_ids:
                    fsc_op_line = fsc_op_line_obj.browse(cr, uid, fsc_op_line_ids)[0]
                    cst_code = fsc_op_line.cst_id.code 
                
                if tax_brw.domain == 'icms':
                    icms_base = taxes['total']
                    icms_value = tax['amount']
                    icms_percent = tax_brw.amount * 100
                    icms_cst = cst_code
                    
                if tax_brw.domain == 'ipi':
                    ipi_base = taxes['total']
                    ipi_value = tax['amount']
                    ipi_percent = tax_brw.amount * 100
                    ipi_cst = cst_code
                
                if tax_brw.domain == 'pis':
                    pis_base = taxes['total'] + ipi_value
                    pis_value = tax['amount']
                    pis_percent = tax_brw.amount * 100
                    pis_cst = cst_code
                
                if tax_brw.domain == 'cofins':
                    cofins_base = taxes['total'] + ipi_value
                    cofins_value = tax['amount']
                    cofins_percent = tax_brw.amount * 100
                    cofins_cst = cst_code

            res[line.id] = {
                    'price_subtotal': taxes['total'] - taxes['total_tax_discount'],
                    'price_total': taxes['total'],
                    'icms_base': icms_base,
                    'icms_value': icms_value,
                    'icms_percent': icms_percent,
                    'icms_cst': icms_cst,
                    'ipi_base': ipi_base,
                    'ipi_value': ipi_value,
                    'ipi_percent': ipi_percent,
                    'ipi_cst': ipi_cst,
                    'pis_base': pis_base,
                    'pis_value': pis_value,
                    'pis_percent': pis_percent,
                    'pis_cst': pis_cst,
                    'cofins_base': cofins_base,
                    'cofins_value': cofins_value,
                    'cofins_percent': cofins_percent,
                    'cofins_cst': cofins_cst,
            }

            if line.invoice_id:
                cur = line.invoice_id.currency_id
                res[line.id] = {
                'price_subtotal': cur_obj.round(cr, uid, cur, res[line.id]['price_subtotal']),
                'price_total': cur_obj.round(cr, uid, cur, res[line.id]['price_total']),
                'icms_base': cur_obj.round(cr, uid, cur, icms_base),
                'icms_value': cur_obj.round(cr, uid, cur, icms_value),
                'icms_percent': icms_percent,
                'icms_cst': icms_cst,
                'ipi_base': cur_obj.round(cr, uid, cur, ipi_base),
                'ipi_value': cur_obj.round(cr, uid, cur, ipi_value),
                'ipi_percent': ipi_percent,
                'ipi_cst': ipi_cst,
                'pis_base': cur_obj.round(cr, uid, cur, pis_base),
                'pis_value': cur_obj.round(cr, uid, cur, pis_value),
                'pis_percent': pis_percent,
                'pis_cst': pis_cst,
                'cofins_base': cur_obj.round(cr, uid, cur, cofins_base),
                'cofins_value': cur_obj.round(cr, uid, cur, cofins_value),
                'cofins_percent': cofins_percent,
                'cofins_cst': cofins_cst,
                }
        return res

    _columns = {
                'cfop_id': fields.many2one('l10n_br_account.cfop', 'CFOP'),
                'price_subtotal': fields.function(_amount_line, method=True, string='Subtotal', type="float",
                                                  digits_compute= dp.get_precision('Account'), store=True, multi='all'),
                'price_total': fields.function(_amount_line, method=True, string='Total', type="float",
                                               digits_compute= dp.get_precision('Account'), store=True, multi='all'),
                'icms_base': fields.function(_amount_line, method=True, string='Base ICMS', type="float",
                                             digits_compute= dp.get_precision('Account'), store=True, multi='all'),
                'icms_value': fields.function(_amount_line, method=True, string='Valor ICMS', type="float",
                                              digits_compute= dp.get_precision('Account'), store=True, multi='all'),
                'icms_percent': fields.function(_amount_line, method=True, string='Perc ICMS', type="float",
                                                digits_compute= dp.get_precision('Account'), store=True, multi='all'),
                'icms_cst': fields.function(_amount_line, method=True, string='CST ICMS', type="char", size=2,
                                            store=True, multi='all'),
                'ipi_base': fields.function(_amount_line, method=True, string='Base IPI', type="float",
                                            digits_compute= dp.get_precision('Account'), store=True, multi='all'),
                'ipi_value': fields.function(_amount_line, method=True, string='Valor IPI', type="float",
                                                  digits_compute= dp.get_precision('Account'), store=True, multi='all'),
                'ipi_percent': fields.function(_amount_line, method=True, string='Perc IPI', type="float",
                                               digits_compute= dp.get_precision('Account'), store=True, multi='all'),
                'ipi_cst': fields.function(_amount_line, method=True, string='CST IPI', type="char", size=2,
                                           store=True, multi='all'),
                'pis_base': fields.function(_amount_line, method=True, string='Base PIS', type="float",
                                                  digits_compute= dp.get_precision('Account'), store=True, multi='all'),
                'pis_value': fields.function(_amount_line, method=True, string='Valor PIS', type="float",
                                             digits_compute= dp.get_precision('Account'), store=True, multi='all'),
                'pis_percent': fields.function(_amount_line, method=True, string='Perc PIS', type="float",
                                               digits_compute= dp.get_precision('Account'), store=True, multi='all'),
                'pis_cst': fields.function(_amount_line, method=True, string='Valor ICMS', type="char", size=2,
                                           store=True, multi='all'),
                'cofins_base': fields.function(_amount_line, method=True, string='Base COFINS', type="float",
                                               digits_compute= dp.get_precision('Account'), store=True, multi='all'),
                'cofins_value': fields.function(_amount_line, method=True, string='Valor COFINS', type="float",
                                                digits_compute= dp.get_precision('Account'), store=True, multi='all'),
                'cofins_percent': fields.function(_amount_line, method=True, string='Perc COFINS', type="float",
                                                  digits_compute= dp.get_precision('Account'), store=True, multi='all'),
                'cofins_cst': fields.function(_amount_line, method=True, string='Valor COFINS', type="char", size=2,
                                              store=True, multi='all'),
                }
                    
    def product_id_change(self, cr, uid, ids, product, uom, qty=0, name='', type='out_invoice', partner_id=False, fposition_id=False, price_unit=False, address_invoice_id=False, currency_id=False, context=None, cfop_id=False):
        
        result = super(account_invoice_line, self).product_id_change(cr, uid, ids, product, uom, qty, name, type, partner_id, fposition_id, price_unit, address_invoice_id, currency_id, context)
        
        if not cfop_id:
            return result

        result['value']['cfop_id'] =  cfop_id

        return result

account_invoice_line()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
