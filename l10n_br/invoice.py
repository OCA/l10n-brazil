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

account_invoice()

class account_invoice_line(osv.osv):
    _inherit = 'account.invoice.line'
    _columns = {
                'cfop_id': fields.many2one('l10n_br.cfop', 'CFOP'),
                }

account_invoice_line()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: