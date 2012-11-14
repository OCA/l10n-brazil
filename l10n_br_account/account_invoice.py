# -*- encoding: utf-8 -*-
###############################################################################
#                                                                             #
# Copyright (C) 2009  Renato Lima - Akretion                                  #
#                                                                             #
#This program is free software: you can redistribute it and/or modify         #
#it under the terms of the GNU Affero General Public License as published by  #
#the Free Software Foundation, either version 3 of the License, or            #
#(at your option) any later version.                                          #
#                                                                             #
#This program is distributed in the hope that it will be useful,              #
#but WITHOUT ANY WARRANTY; without even the implied warranty of               #
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the                #
#GNU Affero General Public License for more details.                          #
#                                                                             #
#You should have received a copy of the GNU Affero General Public License     #
#along with this program.  If not, see <http://www.gnu.org/licenses/>.        #
###############################################################################

from lxml import etree
import time
from datetime import datetime
import netsvc

from osv import fields, osv
from tools.translate import _
import decimal_precision as dp
from sped.nfe.validator import txt

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
                'ii_value': 0.0}
            for line in invoice.invoice_line:
                res[invoice.id]['amount_untaxed'] += line.price_total
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
                res[invoice.id]['ii_value'] += line.ii_value
           
            for invoice_tax in invoice.tax_line:
                if not invoice_tax.tax_code_id.tax_discount:
                    res[invoice.id]['amount_tax'] += invoice_tax.amount

            res[invoice.id]['amount_total'] = res[invoice.id]['amount_tax'] + res[invoice.id]['amount_untaxed']
        return res

    def _get_fiscal_type(self, cr, uid, context=None):
        if context is None:
            context = {}
        return context.get('fiscal_type', 'product')

    def fields_view_get(self, cr, uid, view_id=None, view_type=False,
                        context=None, toolbar=False, submenu=False):
        result = super(account_invoice,self).fields_view_get(
            cr, uid, view_id=view_id, view_type=view_type, context=context,
            toolbar=toolbar, submenu=submenu)

        if context is None:
            context = {}

        field_names = ['service_type_id']
        result['fields'].update(self.fields_get(cr, uid, field_names, context))

        if not view_type:
            view_id = self.pool.get('ir.ui.view').search(cr, uid, [('name', '=', 'account.invoice.tree')])
            view_type = 'tree'

        if view_type == 'form':
            
            eview = etree.fromstring(result['arch'])
            
            if 'type' in context.keys():

                OPERATION_TYPE = {'out_invoice': 'output',
                                  'in_invoice': 'input',
                                  'out_refund': 'input',
                                  'in_refund': 'output'}
                
                JOURNAL_TYPE = {'out_invoice': 'sale',
                                'in_invoice': 'purchase',
                                'out_refund': 'sale_refund',
                                'in_refund': 'purchase_refund'}
                    
                fiscal_types = eview.xpath("//field[@name='invoice_line']")
                for fiscal_type in fiscal_types:
                    fiscal_type.set(
                        'context', "{'type': '%s', 'fiscal_type': '%s'}" % (context['type'],
                                                                            context.get('fiscal_type', 'product')))

                fiscal_categories = eview.xpath("//field[@name='fiscal_category_id']")
                for fiscal_category_id in fiscal_categories:
                    fiscal_category_id.set('domain',
                                           "[('fiscal_type', '=', '%s'), \
                                           ('type', '=', '%s'), \
                                           ('journal_type', '=', '%s')]" \
                                           % (context.get('fiscal_type', 'product'),
                                              OPERATION_TYPE[context['type']],
                                              JOURNAL_TYPE[context['type']]))
                    fiscal_category_id.set('required', '1')
                
                document_series = eview.xpath("//field[@name='document_serie_id']")
                for document_serie_id in document_series:
                    document_serie_id.set('domain', "[('fiscal_type', '=', '%s')]" % (context.get('fiscal_type', 'product')))

            if context.get('fiscal_type', False):
                delivery_infos = eview.xpath("//group[@name='delivery_info']")
                for delivery_info in delivery_infos:
                    delivery_info.set('invisible', '1')

                cfops = eview.xpath("//field[@name='cfop_ids']")
                for cfop_ids in cfops:
                    cfop_ids.set('name', 'service_type_id')
                    cfop_ids.set('domain', '[]')

            result['arch'] = etree.tostring(eview)
        
        if view_type == 'tree':
            doc = etree.XML(result['arch'])
            nodes = doc.xpath("//field[@name='partner_id']")
            partner_string = _('Customer')
            if context.get('type', 'out_invoice') in ('in_invoice', 'in_refund'):
                partner_string = _('Supplier')
            for node in nodes:
                node.set('string', partner_string)
            result['arch'] = etree.tostring(doc)
        return result

    def _get_invoice_line(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('account.invoice.line').browse(cr, uid, ids, context=context):
            result[line.invoice_id.id] = True
        return result.keys()

    def _get_invoice_tax(self, cr, uid, ids, context=None):
        result = {}
        for tax in self.pool.get('account.invoice.tax').browse(cr, uid, ids, context=context):
            result[tax.invoice_id.id] = True
        return result.keys()

    def _get_cfops(self, cr, uid, ids, name, arg, context=None):
        result = {}
        for invoice in self.browse(cr, uid, ids, context=context):
            id = invoice.id
            result[id] = []
            new_ids = []
            for line in invoice.invoice_line:
                if line.cfop_id and not line.cfop_id.id in new_ids:
                    new_ids.append(line.cfop_id.id)
            new_ids.sort()
            result[id] = new_ids
        return result

    def _get_receivable_lines(self, cr, uid, ids, name, arg, context=None):
        res = {}
        for invoice in self.browse(cr, uid, ids, context=context):
            id = invoice.id
            res[id] = []
            if not invoice.move_id:
                continue
            data_lines = [x for x in invoice.move_id.line_id if x.account_id.id == invoice.account_id.id and x.account_id.type in ('receivable', 'payable') and invoice.journal_id.revenue_expense]
            New_ids = []
            for line in data_lines:
                New_ids.append(line.id)
                New_ids.sort()
            res[id] = New_ids
        return res
    
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
        'partner_shipping_id': fields.many2one('res.partner.address', 'Endereço de Entrega', readonly=True, states={'draft': [('readonly', False)]}, help="Shipping address for current sales order."),
        'own_invoice': fields.boolean('Nota Fiscal Própria', readonly=True,
                                      states={'draft':[('readonly',False)]}),
        'internal_number': fields.char('Invoice Number', size=32,
                                       readonly=True,
                                       states={'draft':[('readonly',False)]},
                                       help="Unique number of the invoice, \
                                       computed automatically when the \
                                       invoice is created."),
        'vendor_serie': fields.char('Série NF Entrada', size=12, readonly=True,
                                    states={'draft':[('readonly',False)]},
                                    help="Série do número da Nota Fiscal do \
                                    Fornecedor"),
        'nfe_access_key': fields.char(
            'Chave de Acesso NFE', size=44,
            readonly=True, states={'draft':[('readonly',False)]}),
        'nfe_status': fields.char('Status na Sefaz', size=44, readonly=True),
        'nfe_date': fields.datetime('Data do Status NFE', readonly=True),
        'nfe_export_date': fields.datetime('Exportação NFE', readonly=True),
        'fiscal_document_id': fields.many2one(
            'l10n_br_account.fiscal.document', 'Documento',  readonly=True,
            states={'draft':[('readonly',False)]}),
        'fiscal_document_electronic': fields.related(
            'fiscal_document_id', 'electronic', type='boolean', readonly=True,
            relation='l10n_br_account.fiscal.document', store=True,
            string='Electronic'),
        'fiscal_type': fields.selection([('product', 'Produto'),
                                         ('service', 'Serviço')],
                                        'Tipo Fiscal', requeried=True),
        'move_line_receivable_id': fields.function(
            _get_receivable_lines, method=True, type='many2many',
            relation='account.move.line', string='Entry Lines'),
        'document_serie_id': fields.many2one(
            'l10n_br_account.document.serie', 'Série',
            domain="[('fiscal_document_id','=',fiscal_document_id),\
            ('company_id','=',company_id)]", readonly=True,
            states={'draft':[('readonly',False)]}),
        'fiscal_category_id': fields.many2one(
            'l10n_br_account.fiscal.category', 'Categoria', readonly=True,
            states={'draft':[('readonly',False)]}),
        'fiscal_position': fields.many2one(
            'account.fiscal.position', 'Fiscal Position', readonly=True,
            states={'draft':[('readonly',False)]},
            domain="[('fiscal_category_id','=',fiscal_category_id)]"),
        'cfop_ids': fields.function(
            _get_cfops, method=True, type='many2many',
            relation='l10n_br_account.cfop', string='CFOP'),
        'service_type_id': fields.many2one(
            'l10n_br_account.service.type', 'Tipo de Serviço', readonly=True,
            states={'draft':[('readonly',False)]}),
        'amount_untaxed': fields.function(
            _amount_all, method=True,
            digits_compute=dp.get_precision('Account'), string='Untaxed',
            store={
                'account.invoice': (lambda self, cr, uid, ids, c={}: ids,
                                    ['invoice_line'], 20),
                'account.invoice.tax': (_get_invoice_tax, None, 20),
                'account.invoice.line': (
                    _get_invoice_line, ['price_unit',
                                        'invoice_line_tax_id',
                                        'quantity', 'discount'], 20),
            }, multi='all'),
        'amount_tax': fields.function(
            _amount_all, method=True,
            digits_compute=dp.get_precision('Account'), string='Tax',
            store={
                'account.invoice': (lambda self, cr, uid, ids, c={}: ids,
                                    ['invoice_line'], 20),
                'account.invoice.tax': (_get_invoice_tax, None, 20),
                'account.invoice.line': (_get_invoice_line,
                                         ['price_unit',
                                          'invoice_line_tax_id',
                                          'quantity', 'discount'], 20),
            }, multi='all'),
        'amount_total': fields.function(
            _amount_all, method=True,
            digits_compute=dp.get_precision('Account'), string='Total',
            store={
                'account.invoice': (lambda self, cr, uid, ids, c={}: ids,
                                    ['invoice_line'], 20),
                'account.invoice.tax': (_get_invoice_tax, None, 20),
                'account.invoice.line': (_get_invoice_line,
                                         ['price_unit',
                                          'invoice_line_tax_id',
                                          'quantity', 'discount'], 20),
            }, multi='all'),
        'icms_base': fields.function(
            _amount_all, method=True,
            digits_compute=dp.get_precision('Account'), string='Base ICMS',
            store={
                'account.invoice': (lambda self, cr, uid, ids, c={}: ids,
                                    ['invoice_line'], 20),
                'account.invoice.tax': (_get_invoice_tax, None, 20),
                'account.invoice.line': (_get_invoice_line,
                                         ['price_unit',
                                          'invoice_line_tax_id',
                                          'quantity', 'discount'], 20),
            }, multi='all'),
        'icms_value': fields.function(
            _amount_all, method=True,
            digits_compute=dp.get_precision('Account'), string='Valor ICMS',
            store={
                'account.invoice': (lambda self, cr, uid, ids, c={}: ids,
                                    ['invoice_line'], 20),
                'account.invoice.tax': (_get_invoice_tax, None, 20),
                'account.invoice.line': (_get_invoice_line,
                                         ['price_unit',
                                          'invoice_line_tax_id',
                                          'quantity', 'discount'], 20),
            }, multi='all'),
        'icms_st_base': fields.function(_amount_all, method=True, digits_compute=dp.get_precision('Account'), string='Base ICMS ST',
            store={
                'account.invoice': (lambda self, cr, uid, ids, c={}: ids,
                                    ['invoice_line'], 20),
                'account.invoice.tax': (_get_invoice_tax, None, 20),
                'account.invoice.line': (_get_invoice_line,
                                         ['price_unit',
                                          'invoice_line_tax_id',
                                          'quantity', 'discount'], 20),
            },
            multi='all'),
        'icms_st_value': fields.function(
            _amount_all, method=True,
            digits_compute=dp.get_precision('Account'), string='Valor ICMS ST',
            store={
                'account.invoice': (lambda self, cr, uid, ids, c={}: ids,
                                    ['invoice_line'], 20),
                'account.invoice.tax': (_get_invoice_tax, None, 20),
                'account.invoice.line': (_get_invoice_line,
                                         ['price_unit',
                                          'invoice_line_tax_id',
                                          'quantity', 'discount'], 20),
            }, multi='all'),
        'ipi_base': fields.function(_amount_all, method=True, digits_compute=dp.get_precision('Account'), string='Base IPI',
            store={
                'account.invoice': (lambda self, cr, uid, ids, c={}: ids,
                                    ['invoice_line'], 20),
                'account.invoice.tax': (_get_invoice_tax, None, 20),
                'account.invoice.line': (_get_invoice_line,
                                         ['price_unit',
                                          'invoice_line_tax_id',
                                          'quantity', 'discount'], 20),
            }, multi='all'),
        'ipi_value': fields.function(
            _amount_all, method=True,
            digits_compute=dp.get_precision('Account'), string='Valor IPI',
            store={
                'account.invoice': (lambda self, cr, uid, ids, c={}: ids,
                                    ['invoice_line'], 20),
                'account.invoice.tax': (_get_invoice_tax, None, 20),
                'account.invoice.line': (_get_invoice_line,
                                         ['price_unit',
                                          'invoice_line_tax_id',
                                          'quantity', 'discount'], 20),
            }, multi='all'),
         'pis_base': fields.function(
            _amount_all, method=True,
            digits_compute=dp.get_precision('Account'), string='Base PIS',
            store={
                'account.invoice': (lambda self, cr, uid, ids, c={}: ids,
                                    ['invoice_line'], 20),
                'account.invoice.tax': (_get_invoice_tax, None, 20),
                'account.invoice.line': (_get_invoice_line,
                                         ['price_unit',
                                          'invoice_line_tax_id',
                                          'quantity', 'discount'], 20),
            }, multi='all'),
        'pis_value': fields.function(
            _amount_all, method=True,
            digits_compute=dp.get_precision('Account'), string='Valor PIS',
            store={
                'account.invoice': (lambda self, cr, uid, ids, c={}: ids,
                                    ['invoice_line'], 20),
                'account.invoice.tax': (_get_invoice_tax, None, 20),
                'account.invoice.line': (_get_invoice_line,
                                         ['price_unit',
                                          'invoice_line_tax_id',
                                          'quantity', 'discount'], 20),
            }, multi='all'),
        'cofins_base': fields.function(
            _amount_all, method=True,
            digits_compute=dp.get_precision('Account'), string='Base COFINS',
            store={
                'account.invoice': (lambda self, cr, uid, ids, c={}: ids,
                                    ['invoice_line'], 20),
                'account.invoice.tax': (_get_invoice_tax, None, 20),
                'account.invoice.line': (_get_invoice_line,
                                         ['price_unit',
                                          'invoice_line_tax_id',
                                          'quantity', 'discount'], 20),
            }, multi='all'),
        'cofins_value': fields.function(
            _amount_all, method=True,
            digits_compute=dp.get_precision('Account'), string='Valor COFINS',
            store={
                'account.invoice': (lambda self, cr, uid, ids, c={}: ids,
                                    ['invoice_line'], 20),
                'account.invoice.tax': (_get_invoice_tax, None, 20),
                'account.invoice.line': (_get_invoice_line,
                                         ['price_unit',
                                          'invoice_line_tax_id',
                                          'quantity', 'discount'], 20),
            }, multi='all'),
        'ii_value': fields.function(
            _amount_all, method=True,
            digits_compute=dp.get_precision('Account'), string='Valor II',
            store={
                'account.invoice': (lambda self, cr, uid, ids, c={}: ids,
                                    ['invoice_line'], 20),
                'account.invoice.tax': (_get_invoice_tax, None, 20),
                'account.invoice.line': (_get_invoice_line,
                                         ['price_unit',
                                          'invoice_line_tax_id',
                                          'quantity', 'discount'], 20),
            }, multi='all'),
        'weight': fields.float('Gross weight',readonly=True,
                               states={'draft':[('readonly',False)]},
                               help="The gross weight in Kg.",),
        'weight_net': fields.float('Net weight', help="The net weight in Kg.",
                                    readonly=True,
                                   states={'draft':[('readonly',False)]}),
        'number_of_packages': fields.integer(
            'Volume', readonly=True, states={'draft':[('readonly',False)]}),
        'amount_insurance': fields.float(
            'Valor do Seguro', digits_compute=dp.get_precision('Account'),
            readonly=True, states={'draft':[('readonly',False)]}),
        'amount_costs': fields.float(
            'Outros Custos', digits_compute=dp.get_precision('Account'),
            readonly=True, states={'draft':[('readonly',False)]}),
        'amount_freight': fields.float(
            'Frete', digits_compute=dp.get_precision('Account'),
            readonly=True, states={'draft':[('readonly',False)]}),
    }
    
    def _default_fiscal_category(self, cr, uid, context=None):
        
        DEFAULT_FCATEGORY_PRODUCT = {
            'in_invoice': 'in_invoice_fiscal_category_id', 
            'out_invoice': 'out_invoice_fiscal_category_id',
            'in_refund': 'in_refund_fiscal_category_id', 
            'out_refund': 'out_refund_fiscal_category_id'}
        
        DEFAULT_FCATEGORY_SERVICE = {
            'in_invoice': 'in_invoice_service_fiscal_category_id', 
            'out_invoice': 'out_invoice_service_fiscal_category_id'}
        
        default_fo_category = {
           'product': DEFAULT_FCATEGORY_PRODUCT, 
           'service': DEFAULT_FCATEGORY_SERVICE}
        
        invoice_type = context.get('type', 'out_invoice')
        invoice_fiscal_type = context.get('fiscal_type', 'product')
        
        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        fcategory = self.pool.get('res.company').read(
            cr, uid, user.company_id.id,
            [default_fo_category[invoice_fiscal_type][invoice_type]],
            context=context)[default_fo_category[invoice_fiscal_type][
                invoice_type]]

        return fcategory and fcategory[0] or False

    def _default_fiscal_document(self, cr, uid, context):
        
        invoice_fiscal_type = context.get('fiscal_type', 'product')
        fiscal_invoice_id = invoice_fiscal_type + '_invoice_id'
        
        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        fiscal_document = self.pool.get('res.company').read(
            cr, uid, user.company_id.id, [fiscal_invoice_id],
            context=context)[fiscal_invoice_id]
        
        return fiscal_document and fiscal_document[0] or False
    
    def _default_fiscal_document_serie(self, cr, uid, context):

        invoice_fiscal_type = context.get('fiscal_type', 'product')
        fiscal_document_serie = False
        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        company = self.pool.get('res.company').browse(
            cr, uid, user.company_id.id, context=context)

        if invoice_fiscal_type == 'product':
            fiscal_document_series = [doc_serie for doc_serie in \
                                     company.document_serie_product_ids if \
                                     doc_serie.fiscal_document_id.id == \
                                     company.product_invoice_id.id and \
                                     doc_serie.active]
            if fiscal_document_series:
                fiscal_document_serie = fiscal_document_series[0].id
        else:
            fiscal_document_serie = company.document_serie_service_id and \
            company.document_serie_service_id.id or False

        return fiscal_document_serie

    _defaults = {
        'own_invoice': True,
        'fiscal_type': _get_fiscal_type,
        'fiscal_category_id': _default_fiscal_category,
        'fiscal_document_id': _default_fiscal_document,
        'document_serie_id': _default_fiscal_document_serie}

    def _check_invoice_number(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        invoices = self.browse(cr, uid, ids, context=context)
        domain = []
        for invoice in invoices:
            if not invoice.number:
                continue
            fiscal_document = invoice.fiscal_document_id and invoice.fiscal_document_id.id or False
            domain.extend([('internal_number','=',invoice.number),
                           ('fiscal_type','=',invoice.fiscal_type),
                           ('fiscal_document_id','=',fiscal_document)
                           ])                
            if invoice.own_invoice:
                domain.extend([('company_id','=',invoice.company_id.id),
                              ('internal_number','=',invoice.number),
                              ('fiscal_document_id','=',invoice.fiscal_document_id.id),
                              ('own_invoice','=',True)])
            else:
                domain.extend([('partner_id','=',invoice.partner_id.id),
                              ('vendor_serie','=',invoice.vendor_serie),
                              ('own_invoice','=',False)])
                
            invoice_id = self.pool.get('account.invoice').search(cr, uid, domain)
            if len(invoice_id) > 1:
                    return False
        return True

    _constraints = [
                    (_check_invoice_number,
                     u"Error!\nNão é possível registrar \
                     documentos fiscais com números repetidos.",
                     ['number']),
    ]

    def init(self, cr):
        # Remove a constraint na coluna número do documento fiscal,
        # no caso dos documentos de entradas dos fornecedores pode existir
        # documentos fiscais de fornecedores diferentes com a mesma numeração
        cr.execute("ALTER TABLE %s DROP CONSTRAINT IF EXISTS %s" % ('account_invoice', 'account_invoice_number_uniq'))

    # go from canceled state to draft state
    def action_cancel_draft(self, cr, uid, ids, *args):
        self.write(cr, uid, ids, {'state':'draft', 'internal_number':False, 'nfe_access_key':False, 
                                  'nfe_status':False, 'nfe_date':False, 'nfe_export_date':False})
        wf_service = netsvc.LocalService("workflow")
        for inv_id in ids:
            wf_service.trg_delete(uid, 'account.invoice', inv_id, cr)
            wf_service.trg_create(uid, 'account.invoice', inv_id, cr)
        return True

    def copy(self, cr, uid, id, default={}, context=None):
        default.update({
            'internal_number': False,
            'nfe_access_key': False,
            'nfe_status': False,
            'nfe_date': False,
            'nfe_export_date': False,
        })
        return super(account_invoice, self).copy(cr, uid, id, default, context)

    def action_internal_number(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        
        for obj_inv in self.browse(cr, uid, ids):
            if obj_inv.own_invoice:
                obj_sequence = self.pool.get('ir.sequence')
                seq_no = obj_sequence.get_id(cr, uid, obj_inv.document_serie_id.internal_sequence_id.id, context=context)
                self.write(cr, uid, obj_inv.id, {'internal_number': seq_no})
        
        return True

    def action_number(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        #TODO: not correct fix but required a frech values before reading it.
        self.write(cr, uid, ids, {})

        for obj_inv in self.browse(cr, uid, ids, context=context):
            inv_id = obj_inv.id
            move_id = obj_inv.move_id and obj_inv.move_id.id or False
            ref = obj_inv.internal_number or obj_inv.reference or ''

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

            for inv_id, name in self.name_get(cr, uid, [inv_id]):
                ctx = context.copy()
                if obj_inv.type in ('out_invoice', 'out_refund'):
                    ctx = self.get_log_context(cr, uid, context=ctx)
                message = _('Invoice ') + " '" + name + "' " + _("is validated.")
                self.log(cr, uid, inv_id, message, context=ctx)
        return True

    def action_move_create(self, cr, uid, ids, *args):
        result = super(account_invoice, self).action_move_create(cr, uid, ids, *args)
        for inv in self.browse(cr, uid, ids):
            if inv.move_id:
                self.pool.get('account.move').write(cr, uid, [inv.move_id.id], {'ref': inv.internal_number})
                for move_line in inv.move_id.line_id:    
                    self.pool.get('account.move.line').write(cr, uid, [move_line.id], {'ref': inv.internal_number})   
                move_lines = [x for x in inv.move_id.line_id if x.account_id.id == inv.account_id.id and x.account_id.type in ('receivable', 'payable')]
                i = len(move_lines)
                for move_line in move_lines:
                    move_line_name = '%s/%s' % (inv.internal_number, i)
                    self.pool.get('account.move.line').write(cr, uid, [move_line.id], {'name': move_line_name})   
                    i -= 1
        return result

    def nfe_check(self, cr, uid, ids, context=None):
        
        result = txt.validate(cr, uid, ids, context)
        return result

    def _fiscal_position_map(self, cr, uid, ids, partner_id,
                             partner_invoice_id, company_id,
                             fiscal_category_id):
        result = {'journal_id': False}

        if not fiscal_category_id:
            return result

        obj_company = self.pool.get('res.company').browse(cr, uid, company_id)
        obj_fcategory = self.pool.get('l10n_br_account.fiscal.category')

        fcategory = obj_fcategory.browse(cr, uid, fiscal_category_id)
        result['journal_id'] = fcategory.property_journal and \
        fcategory.property_journal.id or False
        if not result.get('journal_id', False):
            raise osv.except_osv(
                _('Nenhuma Diário !'),
                _("Categoria fisca: '%s', não tem um diário contábil para a \
                empresa %s") % (fcategory.name, obj_company.name))

        obj_rule = self.pool.get('account.fiscal.position.rule')
        fiscal_result = obj_rule.fiscal_position_map(
            cr, uid, partner_id, partner_invoice_id, company_id,
            fiscal_category_id, context={
                'use_domain': ('use_invoice', '=',True)})
        
        result.update(fiscal_result)
        return result

    def onchange_partner_id(self, cr, uid, ids, type, partner_id,
                            date_invoice=False, payment_term=False,
                            partner_bank_id=False, company_id=False,
                            fiscal_category_id=False):

        result = super(account_invoice, self).onchange_partner_id(
            cr, uid, ids, type, partner_id, date_invoice, payment_term,
            partner_bank_id, company_id)

        partner_invoice_id = result['value'].get('address_invoice_id', False)
        fiscal_data = self._fiscal_position_map(cr, uid, ids, partner_id,
                                                partner_invoice_id, company_id,
                                                fiscal_category_id)

        result['value'].update(fiscal_data)
        return result

    def onchange_company_id(self, cr, uid, ids, company_id, partner_id, type,
                            invoice_line, currency_id, address_invoice_id,
                            fiscal_category_id=False):

        result = super(account_invoice, self).onchange_company_id(
            cr, uid, ids, company_id, partner_id, type, invoice_line,
            currency_id, address_invoice_id)

        fiscal_data = self._fiscal_position_map(
            cr, uid, ids, partner_id, address_invoice_id, company_id,
            fiscal_category_id)
        
        result['value'].update(fiscal_data)
        return result

    def onchange_address_invoice_id(self, cr, uid, ids, company_id,
                                    partner_id, address_invoice_id,
                                    fiscal_category_id=False, context=False):

        result = super(account_invoice, self).onchange_address_invoice_id(
            cr,uid,ids,company_id,partner_id,address_invoice_id)
        
        fiscal_data = self._fiscal_position_map(
            cr, uid, ids, partner_id, address_invoice_id, company_id,
            fiscal_category_id)
        
        result['value'].update(fiscal_data)
        return result

    def onchange_fiscal_category_id(self, cr, uid, ids, 
                                    partner_address_id=False,
                                    partner_id=False, company_id=False,
                                    fiscal_category_id=False):
        result = {'value': {}}
        fiscal_data = self._fiscal_position_map(
            cr, uid, ids, partner_id, partner_address_id, company_id,
            fiscal_category_id)
        
        return result['value'].update(fiscal_data)

account_invoice()


class account_invoice_line(osv.osv):
    _inherit = 'account.invoice.line'
    
    def fields_view_get(self, cr, uid, view_id=None, view_type=False, 
                        context=None, toolbar=False, submenu=False):
        
        result = super(account_invoice_line, self).fields_view_get(
            cr, uid, view_id=view_id, view_type=view_type, context=context,
            toolbar=toolbar, submenu=submenu)
        
        if context is None:
            context = {}

        if view_type == 'form':
            
            eview = etree.fromstring(result['arch'])
            
            if 'type' in context.keys():

                OPERATION_TYPE = {'out_invoice': 'output',
                                  'in_invoice': 'input',
                                  'out_refund': 'input',
                                  'in_refund': 'output'}
                
                JOURNAL_TYPE = {'out_invoice': 'sale',
                                'in_invoice': 'purchase',
                                'out_refund': 'sale_refund',
                                'in_refund': 'purchase_refund'}
                    
                fiscal_categories = eview.xpath("//field[@name='fiscal_category_id']")
                for fiscal_category_id in fiscal_categories:
                    fiscal_category_id.set('domain',
                                           "[('type', '=', '%s'), \
                                           ('journal_type', '=', '%s')]" \
                                           % (OPERATION_TYPE[context['type']],
                                              JOURNAL_TYPE[context['type']]))
                    fiscal_category_id.set('required', '1')

                cfops = eview.xpath("//field[@name='cfop_id']")
                for cfop_id in cfops:
                    cfop_id.set('domain', "[('type','=','%s')]" % (
                        OPERATION_TYPE[context['type']],))
                    cfop_id.set('required', '1')
            
            if context.get('fiscal_type', False) == 'service':
                
                cfops = eview.xpath("//field[@name='cfop_id']")
                for cfop_id in cfops:
                    cfop_id.set('invisible', '1')
                    cfop_id.set('required', '0')
            
            product_ids = eview.xpath("//field[@name='product_id']")
            for product_id in product_ids:
                product_id.set('domain', "[('fiscal_type', '=', '%s')]" % (
                    context.get('fiscal_type', 'product'))) 
        
            result['arch'] = etree.tostring(eview)
        
        if view_type == 'tree':
            doc = etree.XML(result['arch'])
            nodes = doc.xpath("//field[@name='partner_id']")
            partner_string = _('Customer')
            if context.get('type', 'out_invoice') in ('in_invoice', 'in_refund'):
                partner_string = _('Supplier')
            for node in nodes:
                node.set('string', partner_string)
            result['arch'] = etree.tostring(doc)
        
        return result
    
    def _amount_tax_icms(self, cr, uid, tax=False):
        result = {
                  'icms_base_type': tax.get('type'),
                  'icms_base': tax.get('total_base', 0.0),
                  'icms_base_other': tax.get('total_base_other', 0.0),
                  'icms_value': tax.get('amount', 0.0),
                  'icms_percent': tax.get('percent', 0.0) * 100,
                  'icms_percent_reduction': tax.get('base_reduction') * 100,
                  }
        return result
    
    def _amount_tax_icmsst(self, cr, uid, tax=False):
        result = {
                  'icms_st_base_type': tax.get('type'),
                  'icms_st_value': tax.get('amount', 0.0),
                  'icms_st_base': tax.get('total_base', 0.0),
                  'icms_st_percent': tax.get('icms_st_percent', 0.0) * 100,
                  'icms_st_percent_reduction': tax.get('icms_st_percent_reduction', 0.0) * 100,
                  'icms_st_mva': tax.get('amount_mva', 0.0) * 100,
                  'icms_st_base_other': tax.get('icms_st_base_other', 0.0),
                  }
        return result
    
    def _amount_tax_ipi(self, cr, uid, tax=False):
        result = {
                  'ipi_type': tax.get('type'),
                  'ipi_base': tax.get('total_base', 0.0),
                  'ipi_value': tax.get('amount', 0.0),
                  'ipi_percent': tax.get('percent', 0.0) * 100,
                  }
        return result
    
    def _amount_tax_cofins(self, cr, uid, tax=False):
        result = {
                  'cofins_base': tax.get('total_base', 0.0),
                  'cofins_base_other': tax.get('total_base_other', 0.0), #FIXME
                  'cofins_value': tax.get('amount', 0.0),
                  'cofins_percent': tax.get('percent', 0.0) * 100,
                  }
        return result
    
    def _amount_tax_cofinsst(self, cr, uid, tax=False):
        result = {
                  'cofins_st_type': 'percent',
                  'cofins_st_base': 0.0,
                  'cofins_st_percent': 0.0,
                  'cofins_st_value': 0.0,
                  }
        return result
    
    def _amount_tax_pis(self, cr, uid, tax=False):
        result = {
                  'pis_base': tax.get('total_base', 0.0),
                  'pis_base_other': tax.get('total_base'),
                  'pis_value': tax.get('amount', 0.0),
                  'pis_percent': tax.get('percent', 0.0) * 100,
                  }
        return result
    
    def _amount_tax_pisst(self, cr, uid, tax=False):
        result = {
                  'pis_st_type': 'percent',
                  'pis_st_base': 0.0,
                  'pis_st_percent': 0.0, 
                  'pis_st_value': 0.0,
                  }
        return result
    
    def _amount_tax_ii(self, cr, uid, tax=False):
        result = {
                  'ii_base': tax.get('total_base', 0.0),
                  'ii_value': tax.get('amount', 0.0),
                  }
        return result
    
    def _amount_tax_issqn(self, cr, uid, taxes=False):
        pass
    
    def _amount_line(self, cr, uid, ids, prop, unknow_none, unknow_dict):
        res = {}
        tax_obj = self.pool.get('account.tax')
        cur_obj = self.pool.get('res.currency')
        for line in self.browse(cr, uid, ids):
            res[line.id] = {
                'price_subtotal': 0.0,
                'price_total': 0.0,
                'icms_base_type': 'percent',
                'icms_base': 0.0,
                'icms_base_other': 0.0,
                'icms_value': 0.0,
                'icms_percent': 0.0,
                'icms_percent_reduction': 0.0,
                'icms_st_base_type': 'percent',
                'icms_st_value': 0.0,
                'icms_st_base': 0.0,
                'icms_st_percent': 0.0,
                'icms_st_percent_reduction': 0.0,
                'icms_st_mva': 0.0,
                'icms_st_base_other': 0.0,
                'icms_cst': '40', #Coloca como isento caso não tenha ICMS
                'ipi_type': 'percent',
                'ipi_base': 0.0,
                'ipi_base_other': 0.0,
                'ipi_value': 0.0,
                'ipi_percent': 0.0,
                'ipi_cst': '53', #Coloca como isento caso não tenha IPI
                'pis_type': 'percent',
                'pis_base': 0.0,
                'pis_base_other': 0.0,
                'pis_value': 0.0,
                'pis_percent': 0.0,
                'pis_st_type': 'percent',
                'pis_st_base': 0.0,
                'pis_st_percent': 0.0, 
                'pis_st_value': 0.0,
                'pis_cst': '99', #Coloca como isento caso não tenha PIS]
                'cofins_type': 'percent',
                'cofins_base': 0.0,
                'cofins_base_other': 0.0,
                'cofins_value': 0.0,
                'cofins_percent': 0.0,
                'cofins_st_type': 'percent',
                'cofins_st_base': 0.0,
                'cofins_st_percent': 0.0,
                'cofins_st_value': 0.0,
                'cofins_cst': '99', #Coloca como isento caso não tenha COFINS
                'ii_base': 0.0,
                'ii_value': 0.0,
            }

            price = line.price_unit * (1-(line.discount or 0.0)/100.0)
            taxes = tax_obj.compute_all(cr, uid, line.invoice_line_tax_id, price, line.quantity, product=line.product_id, address_id=line.invoice_id.address_invoice_id, partner=line.invoice_id.partner_id, fiscal_position=line.fiscal_position)

            icms_cst = '99'
            ipi_cst = '99'
            pis_cst = '99'
            cofins_cst = '99'
            company_id = line.company_id.id and line.invoice_id.company_id.id or False

            # FIXME - AGORA DEVE UTILIZAR AS TAX.CODE DAS LINHAS DA POSIÇÃO FISCAL
            #if line.fiscal_operation_id:

           #     fiscal_operation_ids = self.pool.get('l10n_br_account.fiscal.operation.line').search(cr, uid, [('company_id','=',company_id),('fiscal_operation_id','=',line.fiscal_operation_id.id),('fiscal_classification_id','=',False)], order="fiscal_classification_id")
           #     for fo_line in self.pool.get('l10n_br_account.fiscal.operation.line').browse(cr, uid, fiscal_operation_ids):
           #         if fo_line.tax_code_id.domain == 'icms':
           #             icms_cst = fo_line.cst_id.code
           #         elif fo_line.tax_code_id.domain == 'ipi':
           #             ipi_cst = fo_line.cst_id.code
           #         elif fo_line.tax_code_id.domain == 'pis':
           #             pis_cst = fo_line.cst_id.code
           #         elif fo_line.tax_code_id.domain == 'cofins':
           #             cofins_cst = fo_line.cst_id.code

           #     if line.product_id:
           #         fo_ids_ncm = self.pool.get('l10n_br_account.fiscal.operation.line').search(cr, uid, [('company_id','=',company_id),('fiscal_operation_id','=',line.fiscal_operation_id.id),('fiscal_classification_id','=',line.product_id.property_fiscal_classification.id)])
    
           #         for fo_line_ncm in self.pool.get('l10n_br_account.fiscal.operation.line').browse(cr, uid, fo_ids_ncm):
           #             if fo_line_ncm.tax_code_id.domain == 'icms':
           #                 icms_cst = fo_line_ncm.cst_id.code
           #             elif fo_line_ncm.tax_code_id.domain == 'ipi':
           #                 ipi_cst = fo_line_ncm.cst_id.code
           #             elif fo_line_ncm.tax_code_id.domain == 'pis':
           #                 pis_cst = fo_line_ncm.cst_id.code
           #             elif fo_line_ncm.tax_code_id.domain == 'cofins':
           #                 cofins_cst = fo_line_ncm.cst_id.code

            for tax in taxes['taxes']:
                try:
                    amount_tax = getattr(self, '_amount_tax_%s' % tax.get('domain', ''))
                    res[line.id].update(amount_tax(cr, uid, tax))
                except AttributeError:
                    # Caso não exista campos especificos dos impostos
                    # no documento fiscal, os mesmos são calculados.
                    continue

            if line.invoice_id:
                currency = line.invoice_id.currency_id
                res[line.id].update({
                                'price_subtotal': cur_obj.round(cr, uid, currency, taxes['total'] - taxes['total_tax_discount']),
                                'price_total': cur_obj.round(cr, uid, currency, taxes['total']),
                                'icms_cst': icms_cst,
                                'ipi_cst': ipi_cst,
                                'pis_cst': pis_cst,
                                'cofins_cst': cofins_cst,
                                })

        return res

    _columns = {
        'fiscal_category_id': fields.many2one(
            'l10n_br_account.fiscal.category', 'Categoria'),
        'fiscal_position': fields.many2one(
            'account.fiscal.position', u'Posição Fiscal',
            domain="[('fiscal_category_id','=',fiscal_category_id)]"),
        'cfop_id': fields.many2one('l10n_br_account.cfop', 'CFOP'),
        'price_subtotal': fields.function(
            _amount_line, method=True, string='Subtotal', type="float",
            digits_compute= dp.get_precision('Account'),
            store=True, multi='all'),
        'price_total': fields.function(
            _amount_line, method=True, string='Total', type="float",
            digits_compute= dp.get_precision('Account'),
            store=True, multi='all'),
        'icms_base_type': fields.function(
            _amount_line, method=True, string='Tipo Base ICMS', type="char",
            size=64, store=True, multi='all'),
        'icms_base': fields.function(
            _amount_line, method=True, string='Base ICMS', type="float",
            digits_compute= dp.get_precision('Account'),
            store=True, multi='all'),
        'icms_base_other': fields.function(
            _amount_line, method=True, string='Base ICMS Outras', type="float",
            digits_compute= dp.get_precision('Account'),
            store=True, multi='all'),
        'icms_value': fields.function(
            _amount_line, method=True, string='Valor ICMS', type="float",
            digits_compute= dp.get_precision('Account'),
            store=True, multi='all'),
        'icms_percent': fields.function(
            _amount_line, method=True, string='Perc ICMS', type="float",
            digits_compute= dp.get_precision('Account'),
            store=True, multi='all'),
        'icms_percent_reduction': fields.function(
            _amount_line, method=True, string='Perc Redução de Base ICMS',
            type="float", digits_compute= dp.get_precision('Account'),
            store=True, multi='all'),
        'icms_st_base_type': fields.function(
            _amount_line, method=True, string='Tipo Base ICMS ST', type="char",
            size=64, store=True, multi='all'),
        'icms_st_value': fields.function(
            _amount_line, method=True, string='Valor ICMS ST', type="float",
            digits_compute= dp.get_precision('Account'),
            store=True, multi='all'),
        'icms_st_base': fields.function(
            _amount_line, method=True, string='Base ICMS ST', type="float",
            digits_compute= dp.get_precision('Account'),
            store=True, multi='all'),
        'icms_st_percent': fields.function(
            _amount_line, method=True, string='Percentual ICMS ST',
            type="float", digits_compute= dp.get_precision('Account'),
            store=True, multi='all'),
        'icms_st_percent_reduction': fields.function(
            _amount_line, method=True, string='Perc Redução de Base ICMS ST',
            type="float", digits_compute= dp.get_precision('Account'),
            store=True, multi='all'),
        'icms_st_mva': fields.function(
            _amount_line, method=True, string='MVA ICMS ST', type="float",
            digits_compute= dp.get_precision('Account'),
            store=True, multi='all'),
        'icms_st_base_other': fields.function(
            _amount_line, method=True, string='Base ICMS ST Outras',
            type="float", digits_compute= dp.get_precision('Account'),
            store=True, multi='all'),
        'icms_cst': fields.function(
            _amount_line, method=True, string='CST ICMS', type="char", size=3,
            store=True, multi='all'),
        'ipi_type': fields.function(
            _amount_line, method=True, string='Tipo do IPI', type="char",
            size=64, store=True, multi='all'),
        'ipi_base': fields.function(
            _amount_line, method=True, string='Base IPI', type="float",
            digits_compute= dp.get_precision('Account'),
            store=True, multi='all'),
        'ipi_base_other': fields.function(
            _amount_line, method=True, string='Base IPI Outras', type="float",
            digits_compute= dp.get_precision('Account'),
            store=True, multi='all'),
        'ipi_value': fields.function(
            _amount_line, method=True, string='Valor IPI', type="float",
            digits_compute= dp.get_precision('Account'),
            store=True, multi='all'),
        'ipi_percent': fields.function(
            _amount_line, method=True, string='Perc IPI', type="float",
            digits_compute= dp.get_precision('Account'),
            store=True, multi='all'),
        'ipi_cst': fields.function(
            _amount_line, method=True, string='CST IPI', type="char", size=2,
            store=True, multi='all'),
        'pis_type': fields.function(
            _amount_line, method=True, string='Tipo do PIS',
            type="char", size=64, store=True, multi='all'),
        'pis_base': fields.function(
            _amount_line, method=True, string='Base PIS', type="float",
            digits_compute=dp.get_precision('Account'), store=True,
            multi='all'),
        'pis_base_other': fields.function(
            _amount_line, method=True, string='Base PIS Outras',
            type="float", digits_compute=dp.get_precision('Account'),
            store=True, multi='all'),
        'pis_value': fields.function(
            _amount_line, method=True, string='Valor PIS', type="float",
            digits_compute=dp.get_precision('Account'), store=True,
            multi='all'),
        'pis_percent': fields.function(
            _amount_line, method=True, string='Perc PIS', type="float",
            digits_compute=dp.get_precision('Account'), store=True,
            multi='all'),
        'pis_cst': fields.function(
            _amount_line, method=True, string='CST PIS', type="char",
            size=2, store=True, multi='all'),
        'pis_st_type': fields.function(
            _amount_line, method=True, string='Calculo PIS ST',
            type="char", size=64, store=True, multi='all'),
        'pis_st_base': fields.function(
            _amount_line, method=True, string='Base PIS ST',
            type="float", digits_compute=dp.get_precision('Account'),
            store=True, multi='all'),
        'pis_st_percent': fields.function(
            _amount_line, method=True, string='Perc PIS ST',
            type="float", digits_compute=dp.get_precision('Account'),
            store=True, multi='all'),
        'pis_st_value': fields.function(
            _amount_line, method=True, string='Valor PIS ST',
            type="float", digits_compute=dp.get_precision('Account'),
            store=True, multi='all'),
        'cofins_type': fields.function(
            _amount_line, method=True, string='Tipo do COFINS',
            type="char", size=64, store=True, multi='all'),
        'cofins_base': fields.function(
            _amount_line, method=True, string='Base COFINS',
            type="float", digits_compute=dp.get_precision('Account'),
            store=True, multi='all'),
        'cofins_base_other': fields.function(
            _amount_line, method=True, string='Base COFINS Outras',
            type="float", digits_compute=dp.get_precision('Account'),
            store=True, multi='all'),
        'cofins_value': fields.function(
            _amount_line, method=True, string='Valor COFINS',
            type="float", digits_compute=dp.get_precision('Account'),
            store=True, multi='all'),
        'cofins_percent': fields.function(
            _amount_line, method=True, string='Perc COFINS',
            type="float", digits_compute=dp.get_precision('Account'),
            store=True, multi='all'),
        'cofins_cst': fields.function(
            _amount_line, method=True, string='Valor COFINS',
            type="char", size=2, store=True, multi='all'),
        'cofins_st_type': fields.function(
            _amount_line, method=True, string='Calculo COFINS ST',
            type="char", size=64, store=True, multi='all'),
        'cofins_st_base': fields.function(
            _amount_line, method=True, string='Base COFINS ST',
            type="float", digits_compute=dp.get_precision('Account'),
            store=True, multi='all'),
        'cofins_st_percent': fields.function(
            _amount_line, method=True, string='Perc COFINS ST',
            type="float", digits_compute=dp.get_precision('Account'),
            store=True,  multi='all'),
        'cofins_st_value': fields.function(
            _amount_line, method=True, string='Valor COFINS ST',
            type="float", digits_compute=dp.get_precision('Account'),
            store=True, multi='all'),
        'ii_base': fields.function(
            _amount_line, method=True, string='Base II',
            type="float", digits_compute=dp.get_precision('Account'),
            store=True, multi='all'),
        'ii_value': fields.function(
            _amount_line, method=True, string='Valor II',
            type="float", digits_compute=dp.get_precision('Account'),
            store=True, multi='all'),
        'ii_iof': fields.float(
            'Valor IOF', required=True,
            digits_compute= dp.get_precision('Account')),
        'ii_customhouse_charges': fields.float(
            'Depesas Atuaneiras', required=True,
            digits_compute=dp.get_precision('Account'))}

    _defaults = {
         'ii_iof': 0.0,
         'ii_customhouse_charges': 0.0}

    def _fiscal_position_map(self, cr, uid, ids, partner_id,
                             partner_invoice_id, company_id,
                             fiscal_category_id, product_id=False, 
                             account_id=False, context=None):
        
        if not context:
            context = {}
        
        context['use_domain'] = ('use_invoice', '=', True)
        result = {'cfop_id': False}
        
        obj_rule = self.pool.get('account.fiscal.position.rule')
        fiscal_result = obj_rule.fiscal_position_map(
            cr, uid, partner_id, partner_invoice_id, company_id,
            fiscal_category_id, 
            context=context)
        result.update(fiscal_result)
        if result.get('fiscal_position', False):
            obj_fposition = self.pool.get('account.fiscal.position').browse(
                cr, uid, result['fiscal_position'])
            result['cfop_id'] = obj_fposition.cfop_id.id
            if product_id:
                obj_product = self.pool.get('product.product').browse(
                cr, uid, product_id, context=context)
                if context.get('type') in ('out_invoice', 'out_refund'):
                    context['type_tax_use'] = 'sale'
                    taxes = obj_product.taxes_id and obj_product.taxes_id or (account_id and self.pool.get('account.account').browse(cr, uid, account_id, context=context).tax_ids or False)
                else:
                    context['type_tax_use'] = 'purchase'
                    taxes = obj_product.supplier_taxes_id and obj_product.supplier_taxes_id or (account_id and self.pool.get('account.account').browse(cr, uid, account_id, context=context).tax_ids or False)
    
                tax_ids = self.pool.get('account.fiscal.position').map_tax(
                    cr, uid, obj_fposition, taxes, context)
    
                result['invoice_line_tax_id'] = tax_ids

        return result

    def product_id_change(self, cr, uid, ids, product, uom, qty=0, name='',
                          type='out_invoice', partner_id=False,
                          fposition_id=False, price_unit=False,
                          address_invoice_id=False, currency_id=False,
                          context=None, company_id=False,
                          fiscal_category_id=False, parent_fposition_id=False):

        result = super(account_invoice_line, self).product_id_change(
            cr, uid, ids, product, uom, qty, name, type, partner_id,
            fposition_id, price_unit, address_invoice_id, currency_id,
            context, company_id)

        if not fiscal_category_id or not product or not parent_fposition_id:
            return result

        obj_fp_rule = self.pool.get('account.fiscal.position.rule')
        product_fiscal_category_id = obj_fp_rule.product_fiscal_category_map(
            cr, uid, product, fiscal_category_id)

        fiscal_position = parent_fposition_id or False

        if not product_fiscal_category_id:
            result['value']['fiscal_category_id'] = fiscal_category_id
            result['value']['fiscal_position'] = fiscal_position
            if fiscal_position:
                result['value']['cfop_id'] = self.pool.get('account.fiscal.position').read(cr, uid, [fiscal_position], ['cfop_id'])[0]['cfop_id']
        else:
            result['value']['fiscal_category_id'] = product_fiscal_category_id
            fiscal_data = self._fiscal_position_map(
                cr, uid, ids, partner_id, address_invoice_id, company_id,
                product_fiscal_category_id, product,
                result['value'].get('account_id', False), context)
            result['value'].update(fiscal_data)
        return result
   
    def onchange_fiscal_category_id(self, cr, uid, ids, partner_id,
                                    address_invoice_id, company_id, product_id,
                                    fiscal_category_id, account_id, context):
        result = {'value': {}}
        fiscal_data = self._fiscal_position_map(
            cr, uid, ids, partner_id, address_invoice_id, company_id,
            fiscal_category_id, product_id, account_id, context)
        
        result['value'].update(fiscal_data)
        return result
    
    def onchange_fiscal_position(self, cr, uid, ids, partner_id,
                                    address_invoice_id, company_id, product_id,
                                    fiscal_category_id, account_id, context):
        result = {'value': {}}
        fiscal_data = self._fiscal_position_map(
            cr, uid, ids, partner_id, address_invoice_id, company_id,
            fiscal_category_id, product_id, account_id, context)
        
        result['value'].update(fiscal_data)
        return result

account_invoice_line()
