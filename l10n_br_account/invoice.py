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

import re, string
from unicodedata import normalize
from xml.etree import ElementTree
from xml.etree.ElementTree import Element, SubElement, Comment, tostring
from xml.dom import minidom
from datetime import datetime

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
                'icms_st_base': 0.0,
                'icms_st_value': 0.0,
                'ipi_base': 0.0,
                'ipi_value': 0.0,
                'pis_base': 0.0,
                'pis_value': 0.0,
                'cofins_base': 0.0,
                'cofins_value': 0.0,
            }
            for line in invoice.invoice_line:
                res[invoice.id]['amount_untaxed'] += line.price_total
                res[invoice.id]['amount_tax_discount'] += line.price_total - line.price_subtotal
                res[invoice.id]['icms_base'] += line.icms_base
                res[invoice.id]['icms_value'] += line.icms_value
                res[invoice.id]['icms_st_base'] += line.icms_st_base
                res[invoice.id]['icms_st_value'] += line.icms_st_value
                res[invoice.id]['ipi_base'] += line.ipi_base
                res[invoice.id]['ipi_value'] += line.ipi_value
                res[invoice.id]['pis_base'] += line.pis_base
                res[invoice.id]['pis_value'] += line.pis_value
                res[invoice.id]['cofins_base'] += line.cofins_base
                res[invoice.id]['cofins_value'] += line.cofins_value
                
               
            for invoice_tax in invoice.tax_line:
                    res[invoice.id]['amount_tax'] += invoice_tax.amount
            
            if res[invoice.id]['amount_tax_discount'] > 0 and res[invoice.id]['amount_tax'] > 0:
                res[invoice.id]['amount_tax'] = res[invoice.id]['amount_tax'] - res[invoice.id]['amount_tax_discount']
                
            res[invoice.id]['amount_total'] = res[invoice.id]['amount_tax'] + res[invoice.id]['amount_untaxed'] + res[invoice.id]['icms_st_value']
            
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
            ('sefaz_export','Enviar para Receita'),
            ('sefaz_exception','Erro de autorização da Receita'),
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
        'nfe_access_key': fields.char('Chave de Acesso NFE', size=44, readonly=True, states={'draft':[('readonly',False)]}),
        'nfe_status': fields.char('Status na Sefaz', size=44, readonly=True),
        'nfe_data': fields.date('Data do Status NFE', readonly=True),
        'nfe_data_export': fields.date('Exportação NFE', readonly=True),
        'fiscal_document_id': fields.many2one('l10n_br_account.fiscal.document', 'Documento',  readonly=True, states={'draft':[('readonly',False)]}),
        'fiscal_document_nfe': fields.related('fiscal_document_id', 'nfe', type='boolean', readonly=True, size=64, relation='l10n_br_account.fiscal.document', store=True, string='NFE'),
        'document_serie_id': fields.many2one('l10n_br_account.document.serie', 'Serie', domain="[('fiscal_document_id','=',fiscal_document_id)]", readonly=True, states={'draft':[('readonly',False)]}),
        'fiscal_operation_category_id': fields.many2one('l10n_br_account.fiscal.operation.category', 'Categoria', readonly=True, states={'draft':[('readonly',False)]}),
        'fiscal_operation_id': fields.many2one('l10n_br_account.fiscal.operation', 'Operação Fiscal', domain="[('fiscal_operation_category_id','=',fiscal_operation_category_id)]", readonly=True, states={'draft':[('readonly',False)]}),
        'cfop_id': fields.many2one('l10n_br_account.cfop', 'CFOP', readonly=True, states={'draft':[('readonly',False)]}),
        'vendor_number': fields.char('NF Entrada', size=12, readonly=True, states={'draft':[('readonly',False)]}, help="Número da Nota Fiscal do Fornecedor"),
        'vendor_serie': fields.char('Série NF Entrada', size=12, readonly=True, states={'draft':[('readonly',False)]}, help="Série do número da Nota Fiscal do Fornecedor"),
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
        'icms_st_base': fields.function(_amount_all, method=True, digits_compute=dp.get_precision('Account'), string='Base ICMS ST',
            store={
                'account.invoice': (lambda self, cr, uid, ids, c={}: ids, ['invoice_line'], 20),
                #'account.invoice.tax': (_get_invoice_tax, None, 20),
                #'account.invoice.line': (_get_invoice_line, ['price_unit','invoice_line_tax_id','quantity','discount'], 20),
            },
            multi='all'),
        'icms_st_value': fields.function(_amount_all, method=True, digits_compute=dp.get_precision('Account'), string='Valor ICMS ST',
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
         'pis_base': fields.function(_amount_all, method=True, digits_compute=dp.get_precision('Account'), string='Base PIS',
            store={
                'account.invoice': (lambda self, cr, uid, ids, c={}: ids, ['invoice_line'], 20),
         #       'account.invoice.tax': (_get_invoice_tax, None, 20),
         #       'account.invoice.line': (_get_invoice_line, ['price_unit','invoice_line_tax_id','quantity','discount'], 20),
            },
            multi='all'),
        'pis_value': fields.function(_amount_all, method=True, digits_compute=dp.get_precision('Account'), string='Valor PIS',
            store={
                'account.invoice': (lambda self, cr, uid, ids, c={}: ids, ['invoice_line'], 20),
        #        'account.invoice.tax': (_get_invoice_tax, None, 20),
        #        'account.invoice.line': (_get_invoice_line, ['price_unit','invoice_line_tax_id','quantity','discount'], 20),
            },
            multi='all'),   
        'cofins_base': fields.function(_amount_all, method=True, digits_compute=dp.get_precision('Account'), string='Base COFINS',
            store={
                'account.invoice': (lambda self, cr, uid, ids, c={}: ids, ['invoice_line'], 20),
         #       'account.invoice.tax': (_get_invoice_tax, None, 20),
         #       'account.invoice.line': (_get_invoice_line, ['price_unit','invoice_line_tax_id','quantity','discount'], 20),
            },
            multi='all'),
        'cofins_value': fields.function(_amount_all, method=True, digits_compute=dp.get_precision('Account'), string='Valor COFINS',
            store={
                'account.invoice': (lambda self, cr, uid, ids, c={}: ids, ['invoice_line'], 20),
        #        'account.invoice.tax': (_get_invoice_tax, None, 20),
        #        'account.invoice.line': (_get_invoice_line, ['price_unit','invoice_line_tax_id','quantity','discount'], 20),
            },
            multi='all'),
    }

    def action_internal_number(self, cr, uid, ids, context=None):
        
        if context is None:
            context = {}
        
        for obj_inv in self.browse(cr, uid, ids):
            obj_sequence = self.pool.get('ir.sequence')
            seq_no = obj_sequence.get_id(cr, uid, obj_inv.journal_id.internal_sequence.id, context=context)
            self.write(cr, uid, obj_inv.id, {'internal_number': seq_no})
            
        
        return True

    def action_number(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        #TODO: not correct fix but required a frech values before reading it.
        self.write(cr, uid, ids, {})

        for obj_inv in self.browse(cr, uid, ids):
            id = obj_inv.id
            invtype = obj_inv.type
            number = obj_inv.number
            move_id = obj_inv.move_id and obj_inv.move_id.id or False
            reference = obj_inv.reference or ''

            #self.write(cr, uid, ids, {'internal_number':number})

            if invtype in ('in_invoice', 'in_refund'):
                if not reference:
                    ref = self._convert_ref(cr, uid, number)
                else:
                    ref = reference
            else:
                ref = self._convert_ref(cr, uid, number)

            cr.execute('UPDATE account_move SET ref=%s ' \
                    'WHERE id=%s AND (ref is null OR ref = \'\')',
                    (ref, move_id))
            cr.execute('UPDATE account_move_line SET ref=%s ' \
                    'WHERE move_id=%s AND (ref is null OR ref = \'\')',
                    (ref, move_id))
            cr.execute('UPDATE account_analytic_line SET ref=%s ' \
                    'FROM account_move_line ' \
                    'WHERE account_move_line.move_id = %s ' \
                        'AND account_analytic_line.move_id = account_move_line.id',
                        (ref, move_id))

            for inv_id, name in self.name_get(cr, uid, [id]):
                ctx = context.copy()
                if obj_inv.type in ('out_invoice', 'out_refund'):
                    ctx = self.get_log_context(cr, uid, context=ctx)
                message = _('Invoice ') + " '" + name + "' "+ _("is validated.")
                self.log(cr, uid, inv_id, message, context=ctx)
        return True


    def nfe_dv(self, key):
        
        return '2'

    def nfe_export_txt(self, cr, uid, ids, context=False):

        StrFile = ''

        StrNF = 'NOTA FISCAL|%s|\n' % len(ids)
        
        StrFile = StrNF
        
        for inv in self.browse(cr, uid, ids):
            
            #Endereço do company
            company_addr = self.pool.get('res.partner').address_get(cr, uid, [inv.company_id.partner_id.id], ['default'])
            company_addr_default = self.pool.get('res.partner.address').browse(cr, uid, [company_addr['default']])[0]
            
            #nfe_key = unicode(company_addr_default.state_id.ibge_code).strip().rjust(2, u'0')
            #nfe_key += unicode(datetime.strptime(inv.date_invoice, '%Y-%m-%d').strftime(u'%y%m')).strip().rjust(4, u'0')
            #nfe_key +=  re.sub('[%s]' % re.escape(string.punctuation), '', inv.company_id.partner_id.cnpj_cpf or '')
            #nfe_key += inv.fiscal_document_id.code
            #nfe_key += unicode(inv.document_serie_id.code).strip().rjust(3, u'0')
            #nfe_key += unicode(inv.internal_number).strip().rjust(9, u'0')
            #fe_key += unicode('1').strip().rjust(1, u'0') # Homologação
            #nfe_key += unicode(inv.internal_number).strip().rjust(8, u'0')
            #nfe_key += unicode(self.nfe_dv(nfe_key)).strip().rjust(1, u'0')
            
            StrA = 'A|%s|%s|\n' % ('2.00', '')
            
            StrFile += StrA
            
            StrRegB = {
                       'cUF': company_addr_default.state_id.ibge_code,
                       'cNF': '',
                       'NatOp': normalize('NFKD',unicode(inv.cfop_id.small_name or '')).encode('ASCII','ignore'),
                       'intPag': '2', 
                       'mod': inv.fiscal_document_id.code,
                       'serie': inv.document_serie_id.code,
                       'nNF': inv.internal_number or '',
                       'dEmi': inv.date_invoice or '',
                       'dSaiEnt': inv.date_invoice or '',
                       'hSaiEnt': '',
                       'tpNF': '',
                       'cMunFG': ('%s%s') % (company_addr_default.state_id.ibge_code, company_addr_default.city_id.ibge_code),
                       'TpImp': '1',
                       'TpEmis': '1',
                       'cDV': '',
                       'tpAmb': '2',
                       'finNFe': '1',
                       'procEmi': '0',
                       'VerProc': '2.0.4',
                       'dhCont': '',
                       'xJust': '',
                       }

            if inv.cfop_id.type in ("input"):
                StrRegB['tpNF'] = '0'
            else:
                StrRegB['tpNF'] = '1' 

            StrB = 'B|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|\n' % (StrRegB['cUF'], StrRegB['cNF'], StrRegB['NatOp'], StrRegB['intPag'], 
                                                                                 StrRegB['mod'], StrRegB['serie'], StrRegB['nNF'], StrRegB['dEmi'], StrRegB['dSaiEnt'],
                                                                                 StrRegB['hSaiEnt'], StrRegB['tpNF'], StrRegB['cMunFG'], StrRegB['TpImp'], StrRegB['TpEmis'],
                                                                                 StrRegB['cDV'], StrRegB['tpAmb'], StrRegB['finNFe'], StrRegB['procEmi'], StrRegB['VerProc'], 
                                                                                 StrRegB['dhCont'], StrRegB['xJust'])
            StrFile += StrB
            
            StrRegC = {
                       'XNome': normalize('NFKD',unicode(inv.company_id.partner_id.legal_name or '')).encode('ASCII','ignore'), 
                       'XFant': normalize('NFKD',unicode(inv.company_id.partner_id.name or '')).encode('ASCII','ignore'),
                       'IE': re.sub('[%s]' % re.escape(string.punctuation), '', inv.company_id.partner_id.inscr_est or ''),
                       'IEST': '',
                       'IM': re.sub('[%s]' % re.escape(string.punctuation), '', inv.company_id.partner_id.inscr_mun or ''),
                       'CNAE': '',
                       'CRT': '3',
                       }
            
            StrC = 'C|%s|%s|%s|%s|%s|%s|%s|\n' % (StrRegC['XNome'], StrRegC['XFant'], StrRegC['IE'], StrRegC['IEST'], 
                                                StrRegC['IM'],StrRegC['CNAE'],StrRegC['CRT'])

            StrFile += StrC

            if inv.company_id.partner_id.tipo_pessoa == 'J':
                StrC02 = 'C02|%s|\n' % (re.sub('[%s]' % re.escape(string.punctuation), '', inv.company_id.partner_id.cnpj_cpf or ''))
            else:
                StrC02 = 'C02a|%s|\n' % (re.sub('[%s]' % re.escape(string.punctuation), '', inv.company_id.partner_id.cnpj_cpf or ''))

            StrFile += StrC02

            StrRegC05 = {
                       'XLgr': company_addr_default.street or '', 
                       'Nro': company_addr_default.number or '',
                       'Cpl': normalize('NFKD',unicode(company_addr_default.street2 or '')).encode('ASCII','ignore'),
                       'Bairro': normalize('NFKD',unicode(company_addr_default.district or 'Sem Bairro')).encode('ASCII','ignore'),
                       'CMun': '%s%s' % (company_addr_default.state_id.ibge_code, company_addr_default.city_id.ibge_code),
                       'XMun':  normalize('NFKD',unicode(company_addr_default.city_id.name or '')).encode('ASCII','ignore'),
                       'UF': company_addr_default.state_id.code or '',
                       'CEP': re.sub('[%s]' %  re.escape(string.punctuation), '', str(company_addr_default.zip or '').replace(' ','')),
                       'cPais': company_addr_default.country_id.bc_code or '',
                       'xPais': normalize('NFKD',unicode(company_addr_default.country_id.name or '')).encode('ASCII','ignore'),
                       'fone': re.sub('[%s]' % re.escape(string.punctuation), '', str(company_addr_default.phone or '').replace(' ','')),
                       }

            StrC05 = 'C05|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|\n' % (StrRegC05['XLgr'], StrRegC05['Nro'], StrRegC05['Cpl'], StrRegC05['Bairro'],
                                                                  StrRegC05['CMun'], StrRegC05['XMun'], StrRegC05['UF'], StrRegC05['CEP'],
                                                                  StrRegC05['cPais'], StrRegC05['xPais'], StrRegC05['fone'])

            StrFile += StrC05

            StrRegE = {
                       'xNome': normalize('NFKD',unicode(inv.partner_id.legal_name or '')).encode('ASCII','ignore'), 
                       'IE': re.sub('[%s]' % re.escape(string.punctuation), '', inv.partner_id.inscr_est or ''),
                       'ISUF': '',
                       'email': inv.partner_id.email,
                       }
            
            StrE = 'E|%s|%s|%s|%s|\n' % (StrRegE['xNome'], StrRegE['IE'], StrRegE['ISUF'], StrRegE['email'])

            StrFile += StrE

            if inv.partner_id.tipo_pessoa == 'J':
                StrE0 = 'E02|%s|\n' % (re.sub('[%s]' % re.escape(string.punctuation), '', inv.partner_id.cnpj_cpf or ''))
            else:
                StrE0 = 'E03|%s|\n' % (re.sub('[%s]' % re.escape(string.punctuation), '', inv.partner_id.cnpj_cpf or ''))

            StrFile += StrE0

            StrRegE05 = {
                       'xLgr': inv.address_invoice_id.street or '',
                       'nro': inv.address_invoice_id.number,
                       'xCpl': normalize('NFKD',unicode(inv.address_invoice_id.street2 or '')).encode('ASCII','ignore'),
                       'xBairro': normalize('NFKD',unicode(inv.address_invoice_id.district or 'Sem Bairro')).encode('ASCII','ignore'),
                       'cMun': ('%s%s') % (inv.address_invoice_id.state_id.ibge_code, inv.address_invoice_id.city_id.ibge_code),
                       'xMun': normalize('NFKD',unicode(inv.address_invoice_id.city_id.name or '')).encode('ASCII','ignore'),
                       'UF': inv.address_invoice_id.state_id.code,
                       'CEP': re.sub('[%s]' % re.escape(string.punctuation), '', str(inv.address_invoice_id.zip or '').replace(' ','')),
                       'cPais': inv.address_invoice_id.country_id.bc_code,
                       'xPais': normalize('NFKD',unicode(inv.address_invoice_id.country_id.name or '')).encode('ASCII','ignore'),
                       'fone': re.sub('[%s]' % re.escape(string.punctuation), '', str(inv.address_invoice_id.phone or '').replace(' ','')),
                       }
            
            StrE05 = 'E05|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|\n' % (StrRegE05['xLgr'], StrRegE05['nro'], StrRegE05['xCpl'], StrRegE05['xBairro'],
                                                           StrRegE05['cMun'], StrRegE05['xMun'], StrRegE05['UF'], StrRegE05['CEP'],
                                                           StrRegE05['cPais'],StrRegE05['xPais'], StrRegE05['fone'],)
            
            StrFile += StrE05
            
            i = 0
            for inv_line in inv.invoice_line:
                i += 1
            
                StrH = 'H|%s||\n' % (i)
            
                StrFile += StrH
            
                StrRegI = {
                       'CProd': inv_line.product_id.code,
                       'CEAN': inv_line.product_id.ean13,
                       'XProd': normalize('NFKD',unicode(inv_line.product_id.name or '')).encode('ASCII','ignore'),
                       'NCM': re.sub('[%s]' % re.escape(string.punctuation), '', inv_line.product_id.property_fiscal_classification.name or ''),
                       'EXTIPI': '',
                       'CFOP': inv_line.cfop_id.code,
                       'UCom': inv_line.uos_id.name,
                       'QCom': str("%.4f" % inv_line.quantity),
                       'VUnCom': str("%.2f" % inv_line.price_unit),
                       'VProd': str("%.2f" % inv_line.price_total),
                       'CEANTrib': '',
                       'UTrib': inv_line.uos_id.name,
                       'QTrib': str("%.4f" % inv_line.quantity),
                       'VUnTrib': str("%.2f" % inv_line.price_unit),
                       'VFrete': '',
                       'VSeg': '',
                       'VDesc': '',
                       'vOutro': '',
                       'indTot': '1',
                       'xPed': '',
                       'nItemPed': '',
                       }

                if inv_line.product_id.code:
                        StrRegI['CProd'] = inv_line.product_id.code
                else:
                        StrRegI['CProd'] = unicode(i).strip().rjust(4, u'0')

                if inv_line.discount > 0:
                    StrRegI['VDesc'] = str("%.2f" % inv_line.discount)

                StrI = 'I|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|\n' % (StrRegI['CProd'], StrRegI['CEAN'], StrRegI['XProd'], StrRegI['NCM'],
                                                                                          StrRegI['EXTIPI'], StrRegI['CFOP'], StrRegI['UCom'], StrRegI['QCom'], 
                                                                                          StrRegI['VUnCom'], StrRegI['VProd'], StrRegI['CEANTrib'], StrRegI['UTrib'],
                                                                                          StrRegI['QTrib'], StrRegI['VUnTrib'], StrRegI['VFrete'], StrRegI['VSeg'],
                                                                                          StrRegI['VDesc'], StrRegI['vOutro'], StrRegI['indTot'], StrRegI['xPed'],
                                                                                          StrRegI['nItemPed'])
                
                StrFile += StrI
                
                StrM = 'M|\n'
                
                StrFile += StrM
                
                StrN = 'N|\n'
                
                StrFile += StrN

                StrRegN02 = {
                       'Orig': inv_line.product_id.origin or '0',
                       'CST': inv_line.icms_cst,
                       'ModBC': '0',
                       'VBC': str("%.2f" % inv_line.icms_base),
                       'PICMS': str("%.2f" % inv_line.icms_percent),
                       'VICMS': str("%.2f" % inv_line.icms_value),
                }
                
                #TODO - Fazer alteração para cada tipo de cst
                StrN02 = 'N02|%s|%s|%s|%s|%s|%s|\n' % (StrRegN02['Orig'], StrRegN02['CST'], StrRegN02['ModBC'], StrRegN02['VBC'], StrRegN02['PICMS'],
                                                     StrRegN02['VICMS'])


                StrRegN03 = {
                       'Orig': inv_line.product_id.origin or '0',
                       'CST': inv_line.icms_cst,
                       'ModBC': '0',
                       'VBC': str("%.2f" % inv_line.icms_base),
                       'PICMS': str("%.2f" % inv_line.icms_percent),
                       'VICMS': str("%.2f" % inv_line.icms_value),
                       'ModBCST': '4', #TODO
                       'PMVAST': str("%.2f" % inv_line.icms_st_mva) or '',
                       'PRedBCST': '',
                       'VBCST': str("%.2f" % inv_line.icms_st_base),
                       'PICMSST': str("%.2f" % inv_line.icms_st_percent),
                       'VICMSST': str("%.2f" % inv_line.icms_st_value),
                }

                #TODO - Fazer alteração para cada tipo de cst
                StrN03 = 'N03|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|\n' % (StrRegN03['Orig'], StrRegN03['CST'], StrRegN03['ModBC'], StrRegN03['VBC'], StrRegN03['PICMS'],
                                                                         StrRegN03['VICMS'], StrRegN03['ModBCST'], StrRegN03['PMVAST'], StrRegN03['PRedBCST'], StrRegN03['VBCST'],
                                                                         StrRegN03['PICMSST'], StrRegN03['VICMSST'])
                
                
                StrRegN06 = {
                       'Orig': inv_line.product_id.origin or '0',
                       'CST': inv_line.icms_cst,
                       'vICMS': str("%.2f" % inv_line.icms_value),
                       'motDesICMS': '', #TODO
                }
                
                #TODO - Fazer alteração para cada tipo de cst
                StrN06 = 'N06|%s|%s|%s|%s|\n' % (StrRegN06['Orig'], StrRegN06['CST'], StrRegN06['vICMS'], StrRegN06['motDesICMS'])

                StrRegN09 = {
                       'Orig': inv_line.product_id.origin or '0',
                       'CST': inv_line.icms_cst,
                       'ModBC': '0',
                       'PRedBC': str("%.2f" % inv_line.icms_percent_reduction),
                       'VBC': str("%.2f" % inv_line.icms_base),
                       'PICMS': str("%.2f" % inv_line.icms_percent),
                       'VICMS': str("%.2f" % inv_line.icms_value),
                       'ModBCST': '4', #TODO
                       'PMVAST': str("%.2f" % inv_line.icms_st_mva) or '',
                       'PRedBCST': '',
                       'VBCST': str("%.2f" % inv_line.icms_st_base),
                       'PICMSST': str("%.2f" % inv_line.icms_st_percent),
                       'VICMSST': str("%.2f" % inv_line.icms_st_value),
                }
                
                #TODO - Fazer alteração para cada tipo de cst
                StrN09 = 'N09|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|\n' % (StrRegN09['Orig'], StrRegN09['CST'], StrRegN09['ModBC'], StrRegN09['PRedBC'], StrRegN09['VBC'], StrRegN09['PICMS'], StrRegN09['VICMS'], StrRegN09['ModBCST'], StrRegN09['PMVAST'], StrRegN09['PRedBCST'], StrRegN09['VBCST'], StrRegN09['PICMSST'], StrRegN09['VICMSST'])

                if inv_line.icms_cst in ('00'):
                    StrFile += StrN02
                
                if inv_line.icms_cst in ('10','20'):
                    StrFile += StrN03
                    
                if inv_line.icms_cst in ('40', '41', '50', '51'):
                    StrFile += StrN06
                    
                if inv_line.icms_cst in ('70'):
                    StrFile += StrN09
                
                StrRegO = {
                       'ClEnq': '',
                       'CNPJProd': '',
                       'CSelo': '',
                       'QSelo': '',
                       'CEnq': '999',
                }
                
                StrO = 'O|%s|%s|%s|%s|%s|\n' % (StrRegO['ClEnq'], StrRegO['CNPJProd'], StrRegO['CSelo'], StrRegO['QSelo'], StrRegO['CEnq']) 
                
                StrFile += StrO

                if inv_line.ipi_percent > 0:
                    StrRegO07 = {
                       'CST': inv_line.ipi_cst,
                       'VIPI': str("%.2f" % inv_line.ipi_value),
                    }
                    
                    StrO07 = 'O07|%s|%s|\n' % (StrRegO07['CST'], StrRegO07['VIPI'])
                    
                    StrFile += StrO07 

                    StrRegO10 = {
                       'QUnid': str("%.2f" % inv_line.ipi_base),
                       'VUnid': str("%.2f" % inv_line.ipi_percent),
                    }
                    
                    StrO1 = 'O10|%s|%s|\n' % (StrRegO10['QUnid'], StrRegO10['VUnid'])
                    StrFile += StrO1 
                    
                else:
                    StrO1 = 'O08|%s|\n' % inv_line.ipi_cst
                    StrFile += StrO1
                    
                StrQ = 'Q|\n'
                
                StrFile += StrQ

                if inv_line.pis_percent > 0:
                    StrRegQ02 = {
                       'CST': inv_line.pis_cst,
                       'VBC': str("%.2f" % inv_line.pis_base),
                       'PPIS': str("%.2f" % inv_line.pis_percent),
                       'VPIS': str("%.2f" % inv_line.pis_value),
                    }
                    
                    StrQ02 = ('Q02|%s|%s|%s|%s|\n') % (StrRegQ02['CST'], StrRegQ02['VBC'], StrRegQ02['PPIS'], StrRegQ02['VPIS']) 
                    
                else:
                    StrQ02 = 'Q04|%s|\n' % inv_line.pis_cst
                    
                StrFile += StrQ02
                    
                StrQ = 'S|\n'
                
                StrFile += StrQ

                if inv_line.cofins_percent > 0:
                    StrRegS02 = {
                       'CST': inv_line.cofins_cst,
                       'VBC': str("%.2f" % inv_line.cofins_base),
                       'PCOFINS': str("%.2f" % inv_line.cofins_percent),
                       'VCOFINS': str("%.2f" % inv_line.cofins_value),
                    }

                    StrS02 = ('S02|%s|%s|%s|%s|\n') % (StrRegS02['CST'], StrRegS02['VBC'], StrRegS02['PCOFINS'], StrRegS02['VCOFINS'])
                    
                else:
                    StrS02 = 'S04|%s|\n' % inv_line.cofins_cst

                StrFile += StrS02
                
            StrW = 'W|\n'
            
            StrFile += StrW

            StrRegW02 = {
                         'vBC': str("%.2f" % inv.icms_base),
                         'vICMS': str("%.2f" % inv.icms_value),
                         'vBCST': '0.00',
                         'vST': '0.00',
                         'vProd': str("%.2f" % inv.amount_untaxed),
                         'vFrete': '0.00',
                         'vSeg': str("%.2f" % inv.amount_insurance),
                         'vDesc': '0.00',
                         'vII': '0.00',
                         'vIPI': str("%.2f" % inv.ipi_value),
                         'vPIS': str("%.2f" % inv.pis_value),
                         'vCOFINS': str("%.2f" % inv.cofins_value),
                         'vOutro': str("%.2f" % inv.amount_costs),
                         'vNF': str("%.2f" % inv.amount_total),
                         }
            
            StrW02 = 'W02|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|\n' % (StrRegW02['vBC'], StrRegW02['vICMS'], StrRegW02['vBCST'], StrRegW02['vST'], StrRegW02['vProd'],
                                                                         StrRegW02['vFrete'], StrRegW02['vSeg'], StrRegW02['vDesc'], StrRegW02['vII'], StrRegW02['vIPI'],
                                                                         StrRegW02['vPIS'], StrRegW02['vCOFINS'], StrRegW02['vOutro'], StrRegW02['vNF'])
            
            
            StrFile += StrW02
            
            StrX = 'X|%s|\n' % ('0')
            
            StrFile += StrX
            
            StrRegX03 = {
                      'XNome': '',
                      'IE': '',
                      'XEnder': '',
                      'UF': '',
                      'XMun': '',
                      }
            
            StrX0 = ''
            
            if inv.carrier_id:            
            
                #Endereço da transportadora
                carrier_addr = self.pool.get('res.partner').address_get(cr, uid, [inv.carrier_id.partner_id.id], ['default'])
                carrier_addr_default = self.pool.get('res.partner.address').browse(cr, uid, [carrier_addr['default']])[0]
                
                if inv.carrier_id.partner_id.legal_name:
                    StrX03['XNome'] = inv.carrier_id.partner_id.legal_name 
                else:
                    StrX03['XNome'] = inv.carrier_id.partner_id.name or ''
                
                StrX03['IE'] = inv.carrier_id.partner_id.inscr_est
                StrX03['xEnder'] = carrier_addr_default.street
                StrX03['UF'] = carrier_addr_default.state_id.code
                
                StrX03['xMun'] = carrier_addr_default.city_id.name
                
                if inv.carrier_id.partner_id.tipo_pessoa == 'J':
                    StrX0 = 'X04|%s|\n' %  (inv.carrier_id.partner_id.cnpj_cpf)
                else:
                    StrX0 = 'X05|%s|\n' %  (inv.carrier_id.partner_id.cnpj_cpf)


            StrX03 = 'X03|%s|%s|%s|%s|%s|\n' % (StrRegX03['XNome'], StrRegX03['IE'], StrRegX03['XEnder'], StrRegX03['UF'], StrRegX03['XMun'])
            
            StrFile += StrX03
            StrFile += StrX0
            
            
            StrRegX18 = {
                         'Placa': '',
                         'UF': '',
                         'RNTC': '',
                         }
            
            StrX18 = 'X18|%s|%s|%s|\n' % (StrRegX18['Placa'], StrRegX18['UF'], StrRegX18['RNTC'])
            
            StrFile += StrX18
            
            StrRegX26 = {
                         'QVol': '',
                         'Esp': '', # TODO
                         'Marca': '',
                         'NVol': '',
                         'PesoL': '',
                         'PesoB': '',
                         }
            
            if inv.number_of_packages:

                StrRegX26['QVol'] = inv.number_of_packages
                StrRegX26['Esp'] = 'Volume'
                StrRegX26['Marca']
                StrRegX26['NVol']
                StrRegX26['PesoL'] = inv.weight_net
                StrRegX26['PesoB'] = inv.weight

            StrX26 = 'X26|%s|%s|%s|%s|%s|%s|\n' % (StrRegX26['QVol'], StrRegX26['Esp'], StrRegX26['Marca'], StrRegX26['NVol'], StrRegX26['PesoL'], StrRegX26['PesoB'])

            StrFile += StrX26

            StrRegZ = {
                       'InfAdFisco': '',
                       'InfCpl': '',
                       }
            
            StrZ = 'Z|%s|%s|\n' % (StrRegZ['InfAdFisco'], StrRegZ['InfCpl'])

            StrFile += StrZ
            
        return unicode(StrFile.encode('utf-8'))
            

    def nfe_export_xml(self, cr, uid, ids, context=False):
                
        nfeProc = Element('nfeProc', {'versao': '2.00', 'xmlns': 'http://www.portalfiscal.inf.br/nfe' })
        
        for inv in self.browse(cr, uid, ids):
            
            #Endereço do company
            company_addr = self.pool.get('res.partner').address_get(cr, uid, [inv.company_id.partner_id.id], ['default'])
            company_addr_default = self.pool.get('res.partner.address').browse(cr, uid, [company_addr['default']])[0]
            
            #MontaChave da Nota Fiscal Eletronica
            nfe_key = unicode(company_addr_default.state_id.ibge_code).strip().rjust(2, u'0')
            nfe_key += unicode(datetime.strptime(inv.date_invoice, '%Y-%m-%d').strftime(u'%y%m')).strip().rjust(4, u'0')
            nfe_key +=  '08478495000170' # unicode(inv.company_id.partner_id.cnpj_cpf).strip().rjust(14, u'0')
            nfe_key += inv.fiscal_document_id.code
            nfe_key += unicode(inv.document_serie_id.code).strip().rjust(3, u'0')
            nfe_key += unicode(inv.internal_number).strip().rjust(9, u'0')
            nfe_key += unicode('1').strip().rjust(1, u'0') # Homologação
            nfe_key += unicode(inv.internal_number).strip().rjust(8, u'0')
            nfe_key += unicode(self.nfe_dv(nfe_key)).strip().rjust(1, u'0')
            
            NFe = SubElement(nfeProc, 'NFe', { 'xmlns': 'http://www.portalfiscal.inf.br/nfe' })
            
            infNFe = SubElement(NFe, 'infNFe', {'versao': '2.00', 'Id': nfe_key })

            #Dados da identificação da nota fiscal
            ide = SubElement(infNFe, 'ide')

            ide_cUF = SubElement(ide, 'cUF')
            ide_cUF.text = company_addr_default.state_id.ibge_code
            
            ide_cNF = SubElement(ide, 'cNF')
            ide_cNF.text = unicode(inv.internal_number).strip().rjust(8, u'0')
            
            ide_natOp = SubElement(ide, 'natOp')
            ide_natOp.text = inv.cfop_id.name
            
            ide_indPag = SubElement(ide, 'indPag')
            ide_indPag.text = "2"
            
            ide_mod = SubElement(ide, 'mod')
            ide_mod.text = inv.fiscal_document_id.code 
            
            ide_serie = SubElement(ide, 'serie')
            ide_serie.text = inv.document_serie_id.code
            
            ide_nNF = SubElement(ide, 'nNF')
            ide_nNF.text = inv.internal_number
            
            ide_dEmi = SubElement(ide, 'dEmi')
            ide_dEmi.text = inv.date_invoice
            
            ide_dSaiEnt = SubElement(ide, 'dSaiEnt')
            ide_dSaiEnt.text = inv.date_invoice 
            
            ide_tpNF = SubElement(ide, 'tpNF')
            if inv.type in ("out_invoice", "in_refuld"): 
                ide_tpNF.text = '0'
            else:
                ide_tpNF.text = '1'
            
            ide_cMunFG = SubElement(ide, 'cMunFG')
            ide_cMunFG.text = ('%s%s') % (company_addr_default.state_id.ibge_code, company_addr_default.city_id.ibge_code)
            
            ide_tpImp = SubElement(ide, 'tpImp')
            ide_tpImp.text = "1"
            
            ide_tpEmis = SubElement(ide, 'tpEmis')
            ide_tpEmis.text = "1"
            
            ide_cDV = SubElement(ide, 'cDV')
            ide_cDV.text = self.nfe_dv(nfe_key)
            
            #Tipo de ambiente: 1 - Produção; 2 - Homologação
            ide_tpAmb = SubElement(ide, 'tpAmb')
            ide_tpAmb.text = "2"
            
            #Finalidade da emissão da NF-e: 1 - NFe normal 2 - NFe complementar 3 - NFe de ajuste
            ide_finNFe = SubElement(ide, 'finNFe')
            ide_finNFe.text = "1"
            
            ide_procEmi = SubElement(ide, 'procEmi')
            ide_procEmi.text = "0"
            
            ide_verProc = SubElement(ide, 'verProc')
            ide_verProc.text = "2.0.4"
            
            emit = SubElement(infNFe, 'emit')
            
            emit_CNPJ = SubElement(emit, 'CNPJ')
            emit_CNPJ.text = inv.company_id.partner_id.cnpj_cpf
            
            emit_xNome = SubElement(emit, 'xNome')
            emit_xNome.text = inv.company_id.partner_id.legal_name
            
            emit_xFant = SubElement(emit, 'xFant')
            emit_xFant.text = inv.company_id.partner_id.name
            
            enderEmit = SubElement(emit, 'enderEmit')
            
            enderEmit_xLgr = SubElement(enderEmit, 'xLgr')
            enderEmit_xLgr.text = company_addr_default.street
            
            enderEmit_nro = SubElement(enderEmit, 'nro')
            enderEmit_nro.text = company_addr_default.number
            
            enderEmit_xBairro = SubElement(enderEmit, 'xBairro')
            enderEmit_xBairro.text = company_addr_default.district
            
            enderEmit_cMun = SubElement(enderEmit, 'cMun')
            enderEmit_cMun.text = ('%s%s') % (company_addr_default.state_id.ibge_code, company_addr_default.city_id.ibge_code)
            
            enderEmit_xMun = SubElement(enderEmit, 'xMun')
            enderEmit_xMun.text = company_addr_default.city_id.name
            
            enderEmit_UF = SubElement(enderEmit, 'UF')
            enderEmit_UF.text = company_addr_default.state_id.code
            
            enderEmit_CEP = SubElement(enderEmit, 'CEP')
            enderEmit_CEP.text = company_addr_default.zip
            
            enderEmit_cPais = SubElement(enderEmit, 'cPais')
            enderEmit_cPais.text = company_addr_default.country_id.bc_code
            
            enderEmit_xPais = SubElement(enderEmit, 'xPais')
            enderEmit_xPais.text = company_addr_default.country_id.name
            
            enderEmit_fone = SubElement(enderEmit, 'fone')
            enderEmit_fone.text = company_addr_default.phone
            
            emit_IE = SubElement(emit, 'IE')
            emit_IE.text = inv.company_id.partner_id.inscr_est
            
            emit_IEST = SubElement(emit, 'IEST')
            emit_IEST.text = '0000000000' #FIXME
            
            emit_IM = SubElement(emit, 'IM')
            emit_IM.text = '0000000000' #FIXME
            
            emit_CNAE = SubElement(emit, 'CNAE')
            emit_CNAE.text = '0111301'  #FIXME
            
            emit_CRT = SubElement(emit, 'CRT')
            emit_CRT.text = '3'  #FIXME
            
            dest = SubElement(infNFe, 'dest')
            
            dest_CNPJ = SubElement(dest, 'CNPJ')
            dest_CNPJ.text = inv.partner_id.cnpj_cpf
            
            dest_xNome = SubElement(dest, 'xNome')
            dest_xNome.text = inv.partner_id.legal_name
            
            enderDest = SubElement(dest, 'enderDest')
            
            enderDest_xLgr = SubElement(enderDest, 'xLgr')
            enderDest_xLgr.text = inv.address_invoice_id.street
            
            enderDest_nro = SubElement(enderDest, 'nro')
            enderDest_nro.text = inv.address_invoice_id.number
            
            enderDest_xBairro = SubElement(enderDest, 'xBairro')
            enderDest_xBairro.text = inv.address_invoice_id.district
            
            enderDest_cMun = SubElement(enderDest, 'cMun')
            enderDest_cMun.text = ('%s%s') % (inv.address_invoice_id.state_id.ibge_code, inv.address_invoice_id.city_id.ibge_code)
            
            enderDest_xMun = SubElement(enderDest, 'xMun')
            enderDest_xMun.text = inv.address_invoice_id.city_id.name
            
            enderDest_UF = SubElement(enderDest, 'UF')
            enderDest_UF.text = inv.address_invoice_id.state_id.code
            
            enderDest_CEP = SubElement(enderDest, 'CEP')
            enderDest_CEP.text = inv.address_invoice_id.zip
            
            enderDest_cPais = SubElement(enderDest, 'cPais')
            enderDest_cPais.text = inv.address_invoice_id.country_id.bc_code
            
            enderDest_xPais = SubElement(enderDest, 'xPais')
            enderDest_xPais.text = inv.address_invoice_id.country_id.name
            
            enderDest_fone = SubElement(enderDest, 'fone')
            enderDest_fone.text = inv.address_invoice_id.phone
            
            dest_IE = SubElement(dest, 'IE')
            dest_IE.text = inv.partner_id.inscr_est
            
            for inv_line in inv.invoice_line:
                i =+ 1
                det = SubElement(infNFe, 'det', {'nItem': str(i)})
                
                det_prod = SubElement(det, 'prod')
                
                prod_cProd = SubElement(det_prod, 'cProd')
                if inv_line.product_id.code:
                    prod_cProd.text = inv_line.product_id.code
                else:
                    prod_cProd.text = unicode(i).strip().rjust(4, u'0')
                
                prod_cEAN = SubElement(det_prod, 'cEAN')
                prod_cEAN.text = inv_line.product_id.ean13
                
                prod_xProd = SubElement(det_prod, 'xProd')
                prod_xProd.text = inv_line.product_id.name
                
                prod_NCM = SubElement(det_prod, 'NCM')
                prod_NCM.text = inv_line.product_id.property_fiscal_classification.name
                
                prod_CFOP = SubElement(det_prod, 'CFOP')
                prod_CFOP.text = inv_line.cfop_id.code
                
                prod_uCom = SubElement(det_prod, 'uCom')
                prod_uCom.text = inv_line.uos_id.name
                
                print ElementTree.tostring(infNFe, 'utf-8')
                
                prod_qCom = SubElement(det_prod, 'qCom')
                prod_qCom.text = str("%.4f" % inv_line.quantity)
                
                prod_vUnCom = SubElement(det_prod, 'vUnCom')
                prod_vUnCom.text = str("%.4f" % inv_line.price_unit)
                
                prod_vProd = SubElement(det_prod, 'vProd')
                prod_vProd.text = str("%.2f" % inv_line.price_subtotal)
                        
                prod_cEANTrib = SubElement(det_prod, 'cEANTrib')
                #prod_vProd.text(inv_line.total)
                
                prod_uTrib = SubElement(det_prod, 'uTrib')
                prod_uTrib.text = inv_line.uos_id.name
                
                prod_qTrib = SubElement(det_prod, 'qTrib')
                prod_qTrib.text = '0.0000'  #TODO
                
                prod_vUnTrib = SubElement(det_prod, 'vUnTrib')
                prod_vUnTrib.text = '0.00'  #TODO
                
                prod_vFrete = SubElement(det_prod, 'vFrete')
                prod_vFrete.text = '0.00'  #TODO - Valor do Frete
                
                prod_vSeg = SubElement(det_prod, 'vSeg')
                prod_vSeg.text = '0.00'  #TODO - Valor do seguro

                prod_vDesc = SubElement(det_prod, 'vDesc')
                prod_vDesc.text = str("%.2f" % inv_line.discount)  #TODO
                
                prod_vOutro = SubElement(det_prod, 'vOutro')
                prod_vOutro.text = '0.0000'  #TODO
                
                prod_indTot = SubElement(det_prod, 'indTot')
                prod_indTot.text = '1'  #TODO

                prod_imposto = SubElement(det, 'imposto')

                imposto_icms = SubElement(prod_imposto, 'ICMS' ) # + inv_line.icms_cst)
                
                imposto_icms_cst = SubElement(imposto_icms, 'ICMS%s' % (inv_line.icms_cst))
                
                icms_orig = SubElement(imposto_icms_cst, 'orig')
                icms_orig.text = inv_line.product_id.origin
                
                icms_CST = SubElement(imposto_icms_cst, 'CST')
                icms_CST.text = inv_line.icms_cst
                
                icms_modBC = SubElement(imposto_icms_cst, 'modBC')
                icms_modBC.text = '0' # TODO
                
                icms_vBC = SubElement(imposto_icms_cst, 'vBC')
                icms_vBC.text = str("%.2f" % inv_line.icms_base)
                
                icms_pICMS = SubElement(imposto_icms_cst, 'pICMS')
                icms_pICMS.text = str("%.2f" % inv_line.icms_percent)
                
                icms_vICMS = SubElement(imposto_icms_cst, 'vICMS')
                icms_vICMS.text = str("%.2f" % inv_line.icms_value)
                
                imposto_ipi = SubElement(prod_imposto, 'IPI')
                
                icms_cEnq = SubElement(imposto_ipi, 'cEnq')
                icms_cEnq.text = '999'
                
                #Imposto Não Tributado
                ipi_IPINT = SubElement(imposto_ipi, 'IPINT')
                
                ipi_CST = SubElement(ipi_IPINT, 'CST')
                ipi_CST.text = inv_line.ipi_cst
                
                imposto_pis = SubElement(prod_imposto, 'PIS')
                
                pis_PISAliq = SubElement(imposto_pis, 'PISAliq')
                
                pis_CST = SubElement(pis_PISAliq, 'CST')
                pis_CST.text = inv_line.pis_cst
                
                pis_vBC = SubElement(pis_PISAliq, 'vBC')
                pis_vBC.text = str("%.2f" % inv_line.pis_base)
                
                pis_pPIS = SubElement(pis_PISAliq, 'pPIS')
                pis_pPIS.text = str("%.2f" % inv_line.pis_percent)
                
                pis_vPIS = SubElement(pis_PISAliq, 'vPIS')
                pis_vPIS.text = str("%.2f" % inv_line.pis_value)
                
                imposto_cofins = SubElement(prod_imposto, 'COFINS')
                
                cofins_COFINSAliq = SubElement(imposto_cofins, 'COFINSAliq')
                
                cofins_CST = SubElement(cofins_COFINSAliq, 'CST')
                cofins_CST.text = inv_line.pis_cst
                
                cofins_vBC = SubElement(cofins_COFINSAliq, 'vBC')
                cofins_vBC.text = str("%.2f" % inv_line.cofins_base)
                
                cofins_pCOFINS = SubElement(cofins_COFINSAliq, 'pCOFINS')
                cofins_pCOFINS.text = str("%.2f" % inv_line.cofins_percent)
                
                cofins_vCOFINS = SubElement(cofins_COFINSAliq, 'vCOFINS')
                cofins_vCOFINS.text = str("%.2f" % inv_line.cofins_value)
                
            total = SubElement(infNFe, 'total')
            total_ICMSTot = SubElement(total, 'ICMSTot')
            
            ICMSTot_vBC = SubElement(total_ICMSTot, 'vBC')
            ICMSTot_vBC.text = str("%.2f" % inv.icms_base)
            
            ICMSTot_vICMS = SubElement(total_ICMSTot, 'vICMS')
            ICMSTot_vICMS.text = str("%.2f" % inv.icms_value)
            
            ICMSTot_vBCST = SubElement(total_ICMSTot, 'vBCST')
            ICMSTot_vBCST.text = '0.00' # TODO 
            
            ICMSTot_vST = SubElement(total_ICMSTot, 'vST')
            ICMSTot_vST.text = '0.00' # TODO
            
            ICMSTot_vProd = SubElement(total_ICMSTot, 'vProd')
            ICMSTot_vProd.text = str("%.2f" % inv.amount_untaxed)
            
            ICMSTot_vFrete = SubElement(total_ICMSTot, 'vFrete')
            ICMSTot_vFrete.text = '0.00' # TODO
            
            ICMSTot_vSeg = SubElement(total_ICMSTot, 'vSeg')
            ICMSTot_vSeg.text = str("%.2f" % inv.amount_insurance) 
            
            ICMSTot_vDesc = SubElement(total_ICMSTot, 'vDesc')
            ICMSTot_vDesc.text = '0.00' # TODO
            
            ICMSTot_II = SubElement(total_ICMSTot, 'vII')
            ICMSTot_II.text = '0.00' # TODO
            
            ICMSTot_vIPI = SubElement(total_ICMSTot, 'vIPI')
            ICMSTot_vIPI.text = str("%.2f" % inv.ipi_value)
            
            ICMSTot_vPIS = SubElement(total_ICMSTot, 'vPIS')
            ICMSTot_vPIS.text = str("%.2f" % inv.pis_value)
            
            ICMSTot_vCOFINS = SubElement(total_ICMSTot, 'vCOFINS')
            ICMSTot_vCOFINS.text = str("%.2f" % inv.cofins_value)
            
            ICMSTot_vOutro = SubElement(total_ICMSTot, 'vOutro')
            ICMSTot_vOutro.text = str("%.2f" % inv.amount_costs)
            
            ICMSTot_vNF = SubElement(total_ICMSTot, 'vNF')
            ICMSTot_vNF.text = str("%.2f" % inv.amount_total)
            
            
            transp = SubElement(infNFe, 'transp')
            
            # Modo do Frete: 0- Por conta do emitente; 1- Por conta do destinatário/remetente; 2- Por conta de terceiros; 9- Sem frete (v2.0)
            transp_modFrete = SubElement(transp, 'modFrete')
            transp_modFrete.text = '0' #TODO
            
            if inv.carrier_id:
                
                #Endereço do company
                carrier_addr = self.pool.get('res.partner').address_get(cr, uid, [inv.carrier_id.partner_id.id], ['default'])
                carrier_addr_default = self.pool.get('res.partner.address').browse(cr, uid, [carrier_addr['default']])[0]
                
                transp_transporta = SubElement(transp, 'transporta')
                
                if inv.carrier_id.partner_id.tipo_pessoa == 'J':
                    transporta_CNPJ = SubElement(transp_transporta, 'CNPJ')
                    transporta_CNPJ.text = inv.carrier_id.partner_id.cnpj_cpf
                else:
                    transporta_CPF = SubElement(transp_transporta, 'CPF')
                    transporta_CPF.text = inv.carrier_id.partner_id.cnpj_cpf
                
                transporta_xNome = SubElement(transp_transporta, 'xNome')
                if inv.carrier_id.partner_id.legal_name:
                    transporta_xNome.text = inv.carrier_id.partner_id.legal_name
                else:
                    transporta_xNome.text = inv.carrier_id.partner_id.name
                
                transporta_IE = SubElement(transp_transporta, 'IE')
                transporta_IE.text = inv.carrier_id.partner_id.inscr_est
                
                transporta_xEnder = SubElement(transp_transporta, 'xEnder')
                transporta_xEnder.text = carrier_addr_default.street
                
                transporta_xMun = SubElement(transp_transporta, 'xMun')
                transporta_xMun.text = ('%s%s') % (carrier_addr_default.state_id.ibge_code, carrier_addr_default.city_id.ibge_code)
                
                transporta_UF = SubElement(transp_transporta, 'UF')
                transporta_UF.text = carrier_addr_default.state_id.code
                
            
            if inv.number_of_packages:
                transp_vol = SubElement(transp, 'vol')
            
                vol_qVol = SubElement(transp_vol, 'qVol')
                vol_qVol.text = inv.number_of_packages
                
                vol_esp = SubElement(transp_vol, 'esp')
                vol_esp.text = 'volume' #TODO
                
                vol_pesoL = SubElement(transp_vol, 'pesoL')
                vol_pesoL.text = inv.weight_net
                
                vol_pesoB = SubElement(transp_vol, 'pesoB')
                vol_pesoB.text = inv.weight
            
        xml_string = ElementTree.tostring(nfeProc, 'utf-8')
        return xml_string

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
        #    obj_foperation = self.pool.get('l10n_br_account.fiscal.operation').browse(cr, uid, [obj_fpo.fiscal_operation_id.id])[0]
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
                self.pool.get('account.invoice.line').write(cr, uid, inv_line.id, {'cfop_id': inv.fiscal_operation_id.cfop_id.id})
            
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
                'icms_base_other': 0.0,
                'icms_value': 0.0,
                'icms_percent': 0.0,
                'icms_percent_reduction': 0.0,
                'icms_st_value': 0.0,
                'icms_st_base': 0.0,
                'icms_st_percent': 0.0,
                'icms_st_mva': 0.0,
                'icms_st_base_other': 0.0,
                'icms_cst': '',
                'ipi_base': 0.0,
                'ipi_base_other': 0.0,
                'ipi_value': 0.0,
                'ipi_percent': 0.0,
                'ipi_cst': '',
                'pis_base': 0.0,
                'pis_base_other': 0.0,
                'pis_value': 0.0,
                'pis_percent': 0.0,
                'pis_cst': '',
                'cofins_base': 0.0,
                'cofins_base_other': 0.0,
                'cofins_value': 0.0,
                'cofins_percent': 0.0,
                'cofins_cst': '',
            }
            price = line.price_unit * (1-(line.discount or 0.0)/100.0)
            taxes = tax_obj.compute_all(cr, uid, line.invoice_line_tax_id, price, line.quantity, product=line.product_id, address_id=line.invoice_id.address_invoice_id, partner=line.invoice_id.partner_id)
            
            icms_base = 0.0
            icms_base_other = 0.0
            icms_value = 0.0
            icms_percent = 0.0
            icms_percent_reduction = 0.0
            icms_st_value = 0.0
            icms_st_base = 0.0
            icms_st_percent = 0.0
            icms_st_mva = 0.0
            icms_st_base_other =  0.0
            icms_cst = ''
            ipi_base = 0.0
            ipi_base_other = 0.0
            ipi_value = 0.0
            ipi_percent = 0.0
            ipi_cst = ''
            pis_base = 0.0
            pis_base_other = 0.0
            pis_value = 0.0
            pis_percent = 0.0
            pis_cst = ''
            cofins_base = 0.0
            cofins_base_other = 0.0
            cofins_value = 0.0
            cofins_percent = 0.0
            cofins_cst = ''
            
            for tax in taxes['taxes']:
                fsc_op_line_ids = 0
                fsc_fp_tax_ids = 0
                tax_brw = tax_obj.browse(cr, uid, tax['id'])
                
                if line.invoice_id.fiscal_operation_id:
                    fsc_op_line_ids = fsc_op_line_obj.search(cr, uid, [('company_id','=', line.invoice_id.company_id.id),('fiscal_classification_id','=', line.product_id.property_fiscal_classification.id),('fiscal_operation_id','=',line.invoice_id.fiscal_operation_id.id),('tax_code_id','=', tax_brw.base_code_id.id)])
                
                if line.invoice_id.fiscal_operation_id and not fsc_op_line_ids:
                    fsc_op_line_ids = fsc_op_line_obj.search(cr, uid, [('fiscal_operation_id','=',line.invoice_id.fiscal_operation_id.id),('tax_code_id','=', tax_brw.base_code_id.id)])
                
                
                cst_code = ''
                
                if fsc_op_line_ids:
                    fsc_op_line = fsc_op_line_obj.browse(cr, uid, fsc_op_line_ids)[0]
                    cst_code = fsc_op_line.cst_id.code 
                
                if tax_brw.domain == 'icms':
                    icms_base += tax['total_base']
                    icms_base_other += taxes['total'] - tax['total_base']
                    icms_value += tax['amount']
                    icms_percent += tax_brw.amount * 100
                    icms_percent_reduction += tax_brw.base_reduction * 100
                    icms_cst = icms_cst or cst_code
                
                if tax_brw.domain == 'ipi':
                    ipi_base += tax['total_base']
                    ipi_value += tax['amount']
                    ipi_percent += tax_brw.amount * 100
                    ipi_cst = cst_code
                
                if tax_brw.domain == 'pis':
                    pis_base += tax['total_base']
                    pis_base_other += taxes['total'] - tax['total_base']
                    pis_value += tax['amount'] 
                    pis_percent += tax_brw.amount * 100
                    pis_cst = cst_code
                
                if tax_brw.domain == 'cofins':
                    cofins_base += tax['total_base']
                    cofins_base_other += taxes['total'] - tax['total_base']
                    cofins_value += tax['amount']
                    cofins_percent += tax_brw.amount * 100
                    cofins_cst = cst_code

            for tax_sub in taxes['taxes']:
                tax_brw_sub = tax_obj.browse(cr, uid, tax_sub['id'])
                if tax_brw_sub.domain == 'icmsst':
                    icms_st_value += ((taxes['total'] * (1 + tax_brw_sub.amount_mva)) * (icms_percent / 100)) - icms_value
                    icms_st_base += taxes['total'] * (1 + tax_brw_sub.amount_mva)
                    icms_st_percent += icms_value
                    icms_st_mva += tax_brw_sub.amount_mva * 100
                    icms_st_base_other += 0

            res[line.id] = {
                    'price_subtotal': taxes['total'] - taxes['total_tax_discount'],
                    'price_total': taxes['total'],
                    'icms_base': icms_base,
                    'icms_base_other': icms_base_other,
                    'icms_value': icms_value,
                    'icms_percent': icms_percent,
                    'icms_percent_reduction': icms_percent_reduction,
                    'icms_st_value': icms_st_value,
                    'icms_st_base': icms_st_base,
                    'icms_st_percent' : icms_st_percent,
                    'icms_st_mva' : icms_st_mva,
                    'icms_st_base_other': icms_st_base_other,
                    'icms_cst': icms_cst,
                    'ipi_base': ipi_base,
                    'ipi_base_other': ipi_base_other,
                    'ipi_value': ipi_value,
                    'ipi_percent': ipi_percent,
                    'ipi_cst': ipi_cst,
                    'pis_base': pis_base,
                    'pis_base_other': pis_base_other,
                    'pis_value': pis_value,
                    'pis_percent': pis_percent,
                    'pis_cst': pis_cst,
                    'cofins_base': cofins_base,
                    'cofins_base_other': cofins_base_other,
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
                'icms_base_other': cur_obj.round(cr, uid, cur, icms_base_other),
                'icms_value': cur_obj.round(cr, uid, cur, icms_value),
                'icms_percent': icms_percent,
                'icms_percent_reduction': icms_percent_reduction,
                'icms_st_value': cur_obj.round(cr, uid, cur, icms_st_value),
                'icms_st_base': cur_obj.round(cr, uid, cur, icms_st_base),
                'icms_st_percent' : icms_st_percent,
                'icms_st_mva' : icms_st_mva,
                'icms_st_base_other': cur_obj.round(cr, uid, cur, icms_st_base_other),
                'icms_cst': icms_cst,
                'ipi_base': cur_obj.round(cr, uid, cur, ipi_base),
                'ipi_base_other': cur_obj.round(cr, uid, cur, ipi_base_other),
                'ipi_value': cur_obj.round(cr, uid, cur, ipi_value),
                'ipi_percent': ipi_percent,
                'ipi_cst': ipi_cst,
                'pis_base': cur_obj.round(cr, uid, cur, pis_base),
                'pis_base_other': cur_obj.round(cr, uid, cur, pis_base_other),
                'pis_value': cur_obj.round(cr, uid, cur, pis_value),
                'pis_percent': pis_percent,
                'pis_cst': pis_cst,
                'cofins_base': cur_obj.round(cr, uid, cur, cofins_base),
                'cofins_base_other': cur_obj.round(cr, uid, cur, cofins_base_other),
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
                'icms_base_other': fields.function(_amount_line, method=True, string='Base ICMS Outras', type="float",
                                             digits_compute= dp.get_precision('Account'), store=True, multi='all'),
                'icms_value': fields.function(_amount_line, method=True, string='Valor ICMS', type="float",
                                              digits_compute= dp.get_precision('Account'), store=True, multi='all'),
                'icms_percent': fields.function(_amount_line, method=True, string='Perc ICMS', type="float",
                                                digits_compute= dp.get_precision('Account'), store=True, multi='all'),
                'icms_percent_reduction': fields.function(_amount_line, method=True, string='Perc Redução de Base ICMS', type="float",
                                                digits_compute= dp.get_precision('Account'), store=True, multi='all'),
                'icms_st_value': fields.function(_amount_line, method=True, string='Valor ICMS ST', type="float",
                                              digits_compute= dp.get_precision('Account'), store=True, multi='all'),
                'icms_st_base': fields.function(_amount_line, method=True, string='Base ICMS ST', type="float",
                                              digits_compute= dp.get_precision('Account'), store=True, multi='all'),
                'icms_st_percent': fields.function(_amount_line, method=True, string='Percentual ICMS ST', type="float",
                                              digits_compute= dp.get_precision('Account'), store=True, multi='all'),
                'icms_st_mva': fields.function(_amount_line, method=True, string='MVA ICMS ST', type="float",
                                              digits_compute= dp.get_precision('Account'), store=True, multi='all'),
                'icms_st_base_other': fields.function(_amount_line, method=True, string='Base ICMS ST Outras', type="float",
                                              digits_compute= dp.get_precision('Account'), store=True, multi='all'),
                'icms_cst': fields.function(_amount_line, method=True, string='CST ICMS', type="char", size=2,
                                              store=True, multi='all'),
                'ipi_base': fields.function(_amount_line, method=True, string='Base IPI', type="float",
                                            digits_compute= dp.get_precision('Account'), store=True, multi='all'),
                'ipi_base_other': fields.function(_amount_line, method=True, string='Base IPI Outras', type="float",
                                            digits_compute= dp.get_precision('Account'), store=True, multi='all'),
                'ipi_value': fields.function(_amount_line, method=True, string='Valor IPI', type="float",
                                                  digits_compute= dp.get_precision('Account'), store=True, multi='all'),
                'ipi_percent': fields.function(_amount_line, method=True, string='Perc IPI', type="float",
                                               digits_compute= dp.get_precision('Account'), store=True, multi='all'),
                'ipi_cst': fields.function(_amount_line, method=True, string='CST IPI', type="char", size=2,
                                           store=True, multi='all'),
                'pis_base': fields.function(_amount_line, method=True, string='Base PIS', type="float",
                                                  digits_compute= dp.get_precision('Account'), store=True, multi='all'),
                'pis_base_other': fields.function(_amount_line, method=True, string='Base PIS Outras', type="float",
                                                  digits_compute= dp.get_precision('Account'), store=True, multi='all'),
                'pis_value': fields.function(_amount_line, method=True, string='Valor PIS', type="float",
                                             digits_compute= dp.get_precision('Account'), store=True, multi='all'),
                'pis_percent': fields.function(_amount_line, method=True, string='Perc PIS', type="float",
                                               digits_compute= dp.get_precision('Account'), store=True, multi='all'),
                'pis_cst': fields.function(_amount_line, method=True, string='Valor ICMS', type="char", size=2,
                                           store=True, multi='all'),
                'cofins_base': fields.function(_amount_line, method=True, string='Base COFINS', type="float",
                                               digits_compute= dp.get_precision('Account'), store=True, multi='all'),
                'cofins_base_other': fields.function(_amount_line, method=True, string='Base COFINS Outras', type="float",
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


class account_invoice_tax(osv.osv):
    _inherit = "account.invoice.tax"
    _description = "Invoice Tax"

    def compute(self, cr, uid, invoice_id, context={}):
        tax_grouped = {}
        tax_obj = self.pool.get('account.tax')
        cur_obj = self.pool.get('res.currency')
        inv = self.pool.get('account.invoice').browse(cr, uid, invoice_id, context)
        cur = inv.currency_id
        company_currency = inv.company_id.currency_id.id

        for line in inv.invoice_line:
            taxes = tax_obj.compute_all(cr, uid, line.invoice_line_tax_id, (line.price_unit* (1-(line.discount or 0.0)/100.0)), line.quantity, inv.address_invoice_id.id, line.product_id, inv.partner_id)
            for tax in taxes['taxes']:
                val={}
                val['invoice_id'] = inv.id
                val['name'] = tax['name']
                val['amount'] = tax['amount']
                val['manual'] = False
                val['sequence'] = tax['sequence']
                val['base'] = tax['total_base']

                if inv.type in ('out_invoice','in_invoice'):
                    val['base_code_id'] = tax['base_code_id']
                    val['tax_code_id'] = tax['tax_code_id']
                    val['base_amount'] = cur_obj.compute(cr, uid, inv.currency_id.id, company_currency, val['base'] * tax['base_sign'], context={'date': inv.date_invoice or time.strftime('%Y-%m-%d')}, round=False)
                    val['tax_amount'] = cur_obj.compute(cr, uid, inv.currency_id.id, company_currency, val['amount'] * tax['tax_sign'], context={'date': inv.date_invoice or time.strftime('%Y-%m-%d')}, round=False)
                    val['account_id'] = tax['account_collected_id'] or line.account_id.id
                else:
                    val['base_code_id'] = tax['ref_base_code_id']
                    val['tax_code_id'] = tax['ref_tax_code_id']
                    val['base_amount'] = cur_obj.compute(cr, uid, inv.currency_id.id, company_currency, val['base'] * tax['ref_base_sign'], context={'date': inv.date_invoice or time.strftime('%Y-%m-%d')}, round=False)
                    val['tax_amount'] = cur_obj.compute(cr, uid, inv.currency_id.id, company_currency, val['amount'] * tax['ref_tax_sign'], context={'date': inv.date_invoice or time.strftime('%Y-%m-%d')}, round=False)
                    val['account_id'] = tax['account_paid_id'] or line.account_id.id

                key = (val['tax_code_id'], val['base_code_id'], val['account_id'])
                if not key in tax_grouped:
                    tax_grouped[key] = val
                else:
                    tax_grouped[key]['amount'] += val['amount']
                    tax_grouped[key]['base'] += val['base']
                    tax_grouped[key]['base_amount'] += val['base_amount']
                    tax_grouped[key]['tax_amount'] += val['tax_amount']

        for t in tax_grouped.values():
            t['base'] = cur_obj.round(cr, uid, cur, t['base'])
            t['amount'] = cur_obj.round(cr, uid, cur, t['amount'])
            t['base_amount'] = cur_obj.round(cr, uid, cur, t['base_amount'])
            t['tax_amount'] = cur_obj.round(cr, uid, cur, t['tax_amount'])
        return tax_grouped

    
account_invoice_tax()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
