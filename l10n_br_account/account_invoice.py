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

from openerp import netsvc
from openerp.osv import orm, fields
from openerp.tools.translate import _
from openerp.addons import decimal_precision as dp
from sped.nfe.validator import txt

OPERATION_TYPE = {
    'out_invoice': 'output',
    'in_invoice': 'input',
    'out_refund': 'input',
    'in_refund': 'output'
}

JOURNAL_TYPE = {
    'out_invoice': 'sale',
    'in_invoice': 'purchase',
    'out_refund': 'sale_refund',
    'in_refund': 'purchase_refund'
}


class account_invoice(orm.Model):
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
                'ii_value': 0.0,
                'amount_insurance': 0.0,
                'amount_freight': 0.0,
                'amount_costs': 0.0,
            }
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
                res[invoice.id]['amount_insurance'] += line.insurance_value
                res[invoice.id]['amount_freight'] += line.freight_value
                res[invoice.id]['amount_costs'] += line.other_costs_value

            for invoice_tax in invoice.tax_line:
                if not invoice_tax.tax_code_id.tax_discount:
                    res[invoice.id]['amount_tax'] += invoice_tax.amount

            res[invoice.id]['amount_total'] = res[invoice.id]['amount_tax'] + res[invoice.id]['amount_untaxed']
        return res

    def _get_fiscal_type(self, cr, uid, context=None):
        if context is None:
            context = {}
        return context.get('fiscal_type', 'product')

    # TODO - Melhorar esse método!
    def fields_view_get(self, cr, uid, view_id=None, view_type=False,
                        context=None, toolbar=False, submenu=False):
        result = super(account_invoice, self).fields_view_get(
            cr, uid, view_id=view_id, view_type=view_type, context=context,
            toolbar=toolbar, submenu=submenu)

        if context is None:
            context = {}

        if not view_type:
            view_id = self.pool.get('ir.ui.view').search(
                cr, uid, [('name', '=', 'account.invoice.tree')])
            view_type = 'tree'

        if view_type == 'form':
            eview = etree.fromstring(result['arch'])

            if 'type' in context.keys():
                fiscal_types = eview.xpath("//field[@name='invoice_line']")
                for fiscal_type in fiscal_types:
                    fiscal_type.set(
                        'context', "{'type': '%s', 'fiscal_type': '%s'}" % (
                            context['type'],
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
        for line in self.pool.get('account.invoice.line').browse(
            cr, uid, ids, context=context):
            result[line.invoice_id.id] = True
        return result.keys()

    def _get_invoice_tax(self, cr, uid, ids, context=None):
        result = {}
        for tax in self.pool.get('account.invoice.tax').browse(
            cr, uid, ids, context=context):
            result[tax.invoice_id.id] = True
        return result.keys()

    def _get_cfops(self, cr, uid, ids, name, arg, context=None):
        result = {}
        for invoice in self.browse(cr, uid, ids, context=context):
            result[invoice.id] = []
            new_ids = []
            for line in invoice.invoice_line:
                if line.cfop_id and not line.cfop_id.id in new_ids:
                    new_ids.append(line.cfop_id.id)
            new_ids.sort()
            result[invoice.id] = new_ids
        return result

    def _get_receivable_lines(self, cr, uid, ids, name, arg, context=None):
        res = {}
        for invoice in self.browse(cr, uid, ids, context=context):
            res[invoice.id] = []
            if not invoice.move_id:
                continue
            data_lines = [x for x in invoice.move_id.line_id if x.account_id.id == invoice.account_id.id and x.account_id.type in ('receivable', 'payable') and invoice.journal_id.revenue_expense]
            New_ids = []
            for line in data_lines:
                New_ids.append(line.id)
                New_ids.sort()
            res[invoice.id] = New_ids
        return res

    _columns = {
        'partner_shipping_id': fields.many2one(
            'res.partner', 'Delivery Address',
            readonly=True, required=True,
            states={'draft': [('readonly', False)]},
            help="Delivery address for current sales order."),
        'state': fields.selection([
            ('draft', 'Draft'),
            ('proforma', 'Pro-forma'),
            ('proforma2', 'Pro-forma'),
            ('sefaz_export', 'Enviar para Receita'),
            ('sefaz_exception', 'Erro de autorização da Receita'),
            ('open', 'Open'),
            ('paid', 'Paid'),
            ('cancel', 'Cancelled')
            ], 'State', select=True, readonly=True,
            help=' * The \'Draft\' state is used when a user is encoding a new and unconfirmed Invoice. \
            \n* The \'Pro-forma\' when invoice is in Pro-forma state,invoice does not have an invoice number. \
            \n* The \'Open\' state is used when user create invoice,a invoice number is generated.Its in open state till user does not pay invoice. \
            \n* The \'Paid\' state is set automatically when invoice is paid.\
            \n* The \'sefaz_out\' Gerado aquivo de exportação para sistema daReceita.\
            \n* The \'sefaz_aut\' Recebido arquivo de autolização da Receita.\
            \n* The \'Cancelled\' state is used when user cancel invoice.'),
        'partner_shipping_id': fields.many2one('res.partner', 'Endereço de Entrega', readonly=True, states={'draft': [('readonly', False)]}, help="Shipping address for current sales order."),
        'issuer': fields.selection(
            [('0', 'Emissão própria'),
            ('1', 'Terceiros')], 'Emitente', readonly=True,
            states={'draft': [('readonly', False)]}),
        'nfe_purpose': fields.selection(
            [('1', 'Normal'),
             ('2', 'Complementar'),
             ('3', 'Ajuste')], 'Finalidade da Emissão', readonly=True,
            states={'draft': [('readonly', False)]}),
        'internal_number': fields.char('Invoice Number', size=32,
                                       readonly=True,
                                       states={'draft': [('readonly', False)]},
                                       help="Unique number of the invoice, \
                                       computed automatically when the \
                                       invoice is created."),
        'vendor_serie': fields.char('Série NF Entrada', size=12, readonly=True,
                                    states={'draft': [('readonly', False)]},
                                    help="Série do número da Nota Fiscal do \
                                    Fornecedor"),
        'nfe_access_key': fields.char(
            'Chave de Acesso NFE', size=44,
            readonly=True, states={'draft': [('readonly', False)]}),
        'nfe_status': fields.char('Status na Sefaz', size=44, readonly=True),
        'nfe_date': fields.datetime('Data do Status NFE', readonly=True),
        'nfe_export_date': fields.datetime('Exportação NFE', readonly=True),
        'fiscal_document_id': fields.many2one(
            'l10n_br_account.fiscal.document', 'Documento', readonly=True,
            states={'draft': [('readonly', False)]}),
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
            states={'draft': [('readonly', False)]}),
        'fiscal_category_id': fields.many2one(
            'l10n_br_account.fiscal.category', 'Categoria', readonly=True,
            states={'draft': [('readonly', False)]}),
        'fiscal_position': fields.many2one(
            'account.fiscal.position', 'Fiscal Position', readonly=True,
            states={'draft': [('readonly', False)]},
            domain="[('fiscal_category_id','=',fiscal_category_id)]"),
        'cfop_ids': fields.function(
            _get_cfops, method=True, type='many2many',
            relation='l10n_br_account.cfop', string='CFOP'),
        'fiscal_document_related_ids': fields.one2many(
            'l10n_br_account.document.related', 'invoice_id',
            'Fiscal Document Related', readonly=True,
            states={'draft': [('readonly', False)]}),
        'carrier_name': fields.char('Nome Transportadora', size=32),
        'vehicle_plate': fields.char('Placa do Veiculo', size=7),
        'vehicle_state_id': fields.many2one(
            'res.country.state', 'UF da Placa'),
        'vehicle_l10n_br_city_id': fields.many2one('l10n_br_base.city',
            'Municipio', domain="[('state_id', '=', vehicle_state_id)]"),
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
        'icms_st_base': fields.function(
            _amount_all, method=True,
            digits_compute=dp.get_precision('Account'), string='Base ICMS ST',
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
        'ipi_base': fields.function(
            _amount_all, method=True,
            digits_compute=dp.get_precision('Account'), string='Base IPI',
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
        'weight': fields.float('Gross weight', readonly=True,
                               states={'draft': [('readonly', False)]},
                               help="The gross weight in Kg.",),
        'weight_net': fields.float('Net weight', help="The net weight in Kg.",
                                    readonly=True,
                                    states={'draft': [('readonly', False)]}),
        'number_of_packages': fields.integer(
            'Volume', readonly=True, states={'draft': [('readonly', False)]}),
        'amount_insurance': fields.function(
            _amount_all, method=True,
            digits_compute=dp.get_precision('Account'),
            string='Valor do Seguro',
            store={
                'account.invoice': (lambda self, cr, uid, ids, c={}: ids,
                                    ['invoice_line'], 20),
                'account.invoice.line': (_get_invoice_line,
                                         ['insurance_value'], 20),
            }, multi='all'),
        'amount_freight': fields.function(
            _amount_all, method=True,
            digits_compute=dp.get_precision('Account'),
            string='Valor do Seguro',
            store={
                'account.invoice': (lambda self, cr, uid, ids, c={}: ids,
                                    ['invoice_line'], 20),
                'account.invoice.line': (_get_invoice_line,
                                        ['freight_value'], 20),
            }, multi='all'),
            'amount_costs': fields.function(
        _amount_all, method=True,
        digits_compute=dp.get_precision('Account'), string='Outros Custos',
        store={
            'account.invoice': (lambda self, cr, uid, ids, c={}: ids,
                                ['invoice_line'], 20),
            'account.invoice.line': (_get_invoice_line,
                                     ['other_costs_value'], 20)}, multi='all')
    }

    def _default_fiscal_category(self, cr, uid, context=None):

        DEFAULT_FCATEGORY_PRODUCT = {
            'in_invoice': 'in_invoice_fiscal_category_id',
            'out_invoice': 'out_invoice_fiscal_category_id',
            'in_refund': 'in_refund_fiscal_category_id',
            'out_refund': 'out_refund_fiscal_category_id'
        }

        DEFAULT_FCATEGORY_SERVICE = {
            'in_invoice': 'in_invoice_service_fiscal_category_id',
            'out_invoice': 'out_invoice_service_fiscal_category_id'
        }

        default_fo_category = {
           'product': DEFAULT_FCATEGORY_PRODUCT,
           'service': DEFAULT_FCATEGORY_SERVICE
        }

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
            fiscal_document_series = [doc_serie for doc_serie in
                                     company.document_serie_product_ids if
                                     doc_serie.fiscal_document_id.id ==
                                     company.product_invoice_id.id and
                                     doc_serie.active]
            if fiscal_document_series:
                fiscal_document_serie = fiscal_document_series[0].id
        else:
            fiscal_document_serie = company.document_serie_service_id and \
            company.document_serie_service_id.id or False

        return fiscal_document_serie

    _defaults = {
        'issuer': '0',
        'nfe_purpose': '1',
        'fiscal_type': _get_fiscal_type,
        'fiscal_category_id': _default_fiscal_category,
        'fiscal_document_id': _default_fiscal_document,
        'document_serie_id': _default_fiscal_document_serie
    }

    def _check_invoice_number(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        invoices = self.browse(cr, uid, ids, context=context)
        domain = []
        for invoice in invoices:
            if not invoice.number:
                continue
            fiscal_document = invoice.fiscal_document_id and \
            invoice.fiscal_document_id.id or False
            domain.extend([('internal_number', '=', invoice.number),
                           ('fiscal_type', '=', invoice.fiscal_type),
                           ('fiscal_document_id', '=', fiscal_document)
                           ])
            if invoice.issuer == '0':
                domain.extend(
                    [('company_id', '=', invoice.company_id.id),
                    ('internal_number', '=', invoice.number),
                    ('fiscal_document_id', '=', invoice.fiscal_document_id.id),
                    ('issuer', '=', '0')])
            else:
                domain.extend(
                    [('partner_id', '=', invoice.partner_id.id),
                    ('vendor_serie', '=', invoice.vendor_serie),
                    ('issuer', '=', '1')])

            invoice_id = self.pool.get('account.invoice').search(
                cr, uid, domain)
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
        cr.execute("ALTER TABLE %s DROP CONSTRAINT IF EXISTS %s" % (
            'account_invoice', 'account_invoice_number_uniq'))

    # go from canceled state to draft state
    def action_cancel_draft(self, cr, uid, ids, *args):
        self.write(cr, uid, ids, {
            'state': 'draft',
            'internal_number': False,
            'nfe_access_key': False,
            'nfe_status': False,
            'nfe_date': False,
            'nfe_export_date': False})
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

        for inv in self.browse(cr, uid, ids):
            if inv.issuer == '0':
                sequence = self.pool.get('ir.sequence')
                sequence_read = sequence.read(
                    cr, uid, inv.document_serie_id.internal_sequence_id.id,
                    ['number_next'])
                invalid_number = self.pool.get('l10n_br_account.invoice.invalid.number').search(
                    cr, uid, [('number_start', '<=', sequence_read['number_next']),
                              ('number_end', '>=', sequence_read['number_next']),
                              ('state', '=', 'done')])

                if invalid_number:
                    raise orm.except_orm(
                        _(u'Número Inválido !'),
                        _("O número: %s da série: %s, esta inutilizado") % (
                            sequence_read['number_next'],
                            inv.document_serie_id.name))

                seq_no = sequence.get_id(cr, uid, inv.document_serie_id.internal_sequence_id.id, context=context)
                self.write(cr, uid, inv.id, {'internal_number': seq_no})
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

            cr.execute('UPDATE account_move SET ref=%s '
                'WHERE id=%s AND (ref is null OR ref = \'\')',
                    (ref, move_id))
            cr.execute('UPDATE account_move_line SET ref=%s '
                'WHERE move_id=%s AND (ref is null OR ref = \'\')',
                (ref, move_id))
            cr.execute('UPDATE account_analytic_line SET ref=%s '
                'FROM account_move_line '
                'WHERE account_move_line.move_id = %s '
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

    def _fiscal_position_map(self, cr, uid, result, context=None, **kwargs):

        if not context:
            context = {}
        context.update({'use_domain': ('use_invoice', '=', True)})
        kwargs.update({'context': context})

        if not kwargs.get('fiscal_category_id', False):
            return result

        obj_company = self.pool.get('res.company').browse(
            cr, uid, kwargs.get('company_id', False))
        obj_fcategory = self.pool.get('l10n_br_account.fiscal.category')

        fcategory = obj_fcategory.browse(
            cr, uid, kwargs.get('fiscal_category_id'))
        result['value']['journal_id'] = fcategory.property_journal and \
        fcategory.property_journal.id or False
        if not result['value'].get('journal_id', False):
            raise orm.except_orm(
                _('Nenhum Diário !'),
                _("Categoria fiscal: '%s', não tem um diário contábil para a \
                empresa %s") % (fcategory.name, obj_company.name))

        obj_fp_rule = self.pool.get('account.fiscal.position.rule')
        return obj_fp_rule.apply_fiscal_mapping(cr, uid, result, kwargs)

    def onchange_partner_id(self, cr, uid, ids, type, partner_id,
                            date_invoice=False, payment_term=False,
                            partner_bank_id=False, company_id=False,
                            fiscal_category_id=False):

        result = super(account_invoice, self).onchange_partner_id(
            cr, uid, ids, type, partner_id, date_invoice, payment_term,
            partner_bank_id, company_id)

        return self._fiscal_position_map(
            cr, uid, result, False, partner_id=partner_id,
            partner_invoice_id=partner_id, company_id=company_id,
            fiscal_category_id=fiscal_category_id)

    def onchange_company_id(self, cr, uid, ids, company_id, partner_id, type,
                            invoice_line, currency_id,
                            fiscal_category_id=False):

        result = super(account_invoice, self).onchange_company_id(
            cr, uid, ids, company_id, partner_id, type, invoice_line,
            currency_id)

        return self._fiscal_position_map(
            cr, uid, result, False, partner_id=partner_id,
            partner_invoice_id=partner_id, company_id=company_id,
            fiscal_category_id=fiscal_category_id)

    def onchange_fiscal_category_id(self, cr, uid, ids,
                                    partner_address_id=False,
                                    partner_id=False, company_id=False,
                                    fiscal_category_id=False):
        result = {'value': {}}
        return self._fiscal_position_map(
            cr, uid, result, False, partner_id=partner_id,
            partner_invoice_id=partner_id, company_id=company_id,
            fiscal_category_id=fiscal_category_id)

    def onchange_fiscal_document_id(self, cr, uid, ids, fiscal_document_id,
                                    company_id, issuer, fiscal_type,
                                    context=None):
        result = {'value': {'document_serie_id': False}}
        if not context:
            context = {}
        company = self.pool.get('res.company').browse(cr, uid, company_id,
            context=context)

        if issuer == '0':
            serie = False
            if fiscal_type == 'product':
                series = [doc_serie.id for doc_serie in
                    company.document_serie_product_ids if
                    doc_serie.fiscal_document_id.id == fiscal_document_id and
                    doc_serie.active]
                if series:
                    serie = series[0]
            else:
                serie = company.document_serie_service_id and \
                company.document_serie_service_id.id or False
            result['value']['document_serie_id'] = serie

        return result


class account_invoice_line(orm.Model):
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

        return result

    def _amount_line(self, cr, uid, ids, prop, unknow_none, unknow_dict):
        res = {}
        tax_obj = self.pool.get('account.tax')
        cur_obj = self.pool.get('res.currency')
        for line in self.browse(cr, uid, ids):
            res[line.id] = {
                'price_subtotal': 0.0,
                'price_total': 0.0,
            }

            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            taxes = tax_obj.compute_all(
                cr, uid, line.invoice_line_tax_id, price, line.quantity,
                line.product_id, line.invoice_id.partner_id,
                fiscal_position=line.fiscal_position,
                insurance_value=line.insurance_value,
                freight_value=line.freight_value,
                other_costs_value=line.other_costs_value)

            if line.invoice_id:
                currency = line.invoice_id.currency_id
                res[line.id].update({
                    'price_subtotal': cur_obj.round(
                        cr, uid, currency,
                        taxes['total'] - taxes['total_tax_discount']),
                    'price_total': cur_obj.round(
                        cr, uid, currency, taxes['total']),
                })

        return res

    _columns = {
        'fiscal_category_id': fields.many2one(
            'l10n_br_account.fiscal.category', 'Categoria'),
        'fiscal_position': fields.many2one(
            'account.fiscal.position', u'Posição Fiscal',
            domain="[('fiscal_category_id','=',fiscal_category_id)]"),
        'cfop_id': fields.many2one('l10n_br_account.cfop', 'CFOP'),
        'fiscal_classification_id': fields.many2one(
            'account.product.fiscal.classification', 'Classficação Fiscal'),
        'product_type': fields.selection(
            [('product', 'Produto'), ('service', u'Serviço')],
            'Tipo do Produto', required=True),
        'price_subtotal': fields.function(
            _amount_line, method=True, string='Subtotal', type="float",
            digits_compute=dp.get_precision('Account'),
            store=True, multi='all'),
        'price_total': fields.function(
            _amount_line, method=True, string='Total', type="float",
            digits_compute=dp.get_precision('Account'),
            store=True, multi='all'),
        'icms_manual': fields.boolean('ICMS Manual?'),
        'icms_origin': fields.selection(
            [('0', '0 - Nacional, exceto as indicadas nos códigos 3 a 5'),
            ('1', '1 - Estrangeira - Importação direta, exceto a indicada no código 6'),
            ('2', '2 - Estrangeira - Adquirida no mercado interno, exceto a indicada no código 7'),
            ('3', '3 - Nacional, mercadoria ou bem com Conteúdo de Importação superior a  40% (quarenta por cento)'),
            ('4', '4 - Nacional, cuja produção tenha sido feita em conformidade com os processos produtivos básicos de que tratam o Decreto-Lei nº 288/67, e as Leis nºs 8.248/91, 8.387/91, 10.176/01 e 11.484/07'),
            ('5', '5 - Nacional, mercadoria ou bem com Conteúdo de Importação inferior ou igual a 40% (quarenta por cento)'),
            ('6', '6 - Estrangeira - Importação direta, sem similar nacional, constante em lista de Resolução CAMEX'),
            ('7', '7 - Estrangeira - Adquirida no mercado interno, sem similar nacional, constante em lista de Resolução CAMEX')],
            'Origem'),
        'icms_base_type': fields.selection(
            [('0', 'Margem Valor Agregado (%)'), ('1', 'Pauta (valor)'),
            ('2', 'Preço Tabelado Máximo (valor)'),
            ('3', 'Valor da Operação')],
            'Tipo Base ICMS', required=True),
        'icms_base': fields.float('Base ICMS', required=True,
            digits_compute=dp.get_precision('Account')),
        'icms_base_other': fields.float('Base ICMS Outras', required=True,
            digits_compute=dp.get_precision('Account')),
        'icms_value': fields.float('Valor ICMS', required=True,
            digits_compute=dp.get_precision('Account')),
        'icms_percent': fields.float('Perc ICMS',
            digits_compute=dp.get_precision('Discount')),
        'icms_percent_reduction': fields.float('Perc Redução de Base ICMS',
            digits_compute=dp.get_precision('Discount')),
        'icms_st_base_type': fields.selection(
            [('0', 'Preço tabelado ou máximo  sugerido'),
            ('1', 'Lista Negativa (valor)'),
            ('2', 'Lista Positiva (valor)'), ('3', 'Lista Neutra (valor)'),
            ('4', 'Margem Valor Agregado (%)'), ('5', 'Pauta (valor)')],
            'Tipo Base ICMS ST', required=True),
        'icms_st_value': fields.float('Valor ICMS ST', required=True,
            digits_compute=dp.get_precision('Account')),
        'icms_st_base': fields.float('Base ICMS ST', required=True,
            digits_compute=dp.get_precision('Account')),
        'icms_st_percent': fields.float('Percentual ICMS ST',
            digits_compute=dp.get_precision('Discount')),
        'icms_st_percent_reduction': fields.float(
            'Perc Redução de Base ICMS ST',
            digits_compute=dp.get_precision('Discount')),
        'icms_st_mva': fields.float('MVA ICMS ST',
            digits_compute=dp.get_precision('Discount')),
        'icms_st_base_other': fields.float('Base ICMS ST Outras',
            required=True, digits_compute=dp.get_precision('Account')),
        'icms_cst_id': fields.many2one('account.tax.code', 'CST ICMS',
            domain=[('domain', '=', 'icms')]),
        'issqn_manual': fields.boolean('ISSQN Manual?'),
        'issqn_type': fields.selection(
            [('N', 'Normal'), ('R', 'Retida'),
            ('S', 'Substituta'), ('I', 'Isenta')], 'Tipo do ISSQN',
            required=True),
        'service_type_id': fields.many2one(
            'l10n_br_account.service.type', 'Tipo de Serviço'),
        'issqn_base': fields.float('Base ISSQN', required=True,
            digits_compute=dp.get_precision('Account')),
        'issqn_percent': fields.float('Perc ISSQN', required=True,
            digits_compute=dp.get_precision('Discount')),
        'issqn_value': fields.float('Valor ISSQN', required=True,
            digits_compute=dp.get_precision('Account')),
        'ipi_manual': fields.boolean('IPI Manual?'),
        'ipi_type': fields.selection(
            [('percent', 'Percentual'), ('quantity', 'Em Valor')],
            'Tipo do IPI', required=True),
        'ipi_base': fields.float('Base IPI', required=True,
            digits_compute=dp.get_precision('Account')),
        'ipi_base_other': fields.float('Base IPI Outras', required=True,
            digits_compute=dp.get_precision('Account')),
        'ipi_value': fields.float('Valor IPI', required=True,
            digits_compute=dp.get_precision('Account')),
        'ipi_percent': fields.float('Perc IPI', required=True,
            digits_compute=dp.get_precision('Discount')),
        'ipi_cst_id': fields.many2one('account.tax.code', 'CST IPI',
            domain=[('domain', '=', 'ipi')]),
        'pis_manual': fields.boolean('PIS Manual?'),
        'pis_type': fields.selection(
            [('percent', 'Percentual'), ('quantity', 'Em Valor')],
            'Tipo do PIS', required=True),
        'pis_base': fields.float('Base PIS', required=True,
            digits_compute=dp.get_precision('Account')),
        'pis_base_other': fields.float('Base PIS Outras', required=True,
            digits_compute=dp.get_precision('Account')),
        'pis_value': fields.float('Valor PIS', required=True,
            digits_compute=dp.get_precision('Account')),
        'pis_percent': fields.float('Perc PIS', required=True,
            digits_compute=dp.get_precision('Discount')),
        'pis_cst_id': fields.many2one('account.tax.code', 'CST PIS',
            domain=[('domain', '=', 'pis')]),
        'pis_st_type': fields.selection(
            [('percent', 'Percentual'), ('quantity', 'Em Valor')],
            'Tipo do PIS ST', required=True),
        'pis_st_base': fields.float('Base PIS ST', required=True,
            digits_compute=dp.get_precision('Account')),
        'pis_st_percent': fields.float('Perc PIS ST', required=True,
            digits_compute=dp.get_precision('Account')),
        'pis_st_value': fields.float('Valor PIS ST', required=True,
            digits_compute=dp.get_precision('Account')),
        'cofins_manual': fields.boolean('COFINS Manual?'),
        'cofins_type': fields.selection(
            [('percent', 'Percentual'), ('quantity', 'Em Valor')],
            'Tipo do COFINS', required=True),
        'cofins_base': fields.float('Base COFINS', required=True,
            digits_compute=dp.get_precision('Account')),
        'cofins_base_other': fields.float('Base COFINS Outras', required=True,
            digits_compute=dp.get_precision('Account')),
        'cofins_value': fields.float('Valor COFINS', required=True,
            digits_compute=dp.get_precision('Account')),
        'cofins_percent': fields.float('Perc COFINS', required=True,
            digits_compute=dp.get_precision('Discount')),
        'cofins_cst_id': fields.many2one('account.tax.code', 'CST PIS',
            domain=[('domain', '=', 'cofins')]),
        'cofins_st_type': fields.selection(
            [('percent', 'Percentual'), ('quantity', 'Em Valor')],
            'Tipo do COFINS ST', required=True),
        'cofins_st_base': fields.float('Base COFINS ST', required=True,
            digits_compute=dp.get_precision('Account')),
        'cofins_st_percent': fields.float('Perc COFINS ST', required=True,
            digits_compute=dp.get_precision('Discount')),
        'cofins_st_value': fields.float('Valor COFINS ST', required=True,
            digits_compute=dp.get_precision('Account')),
        'ii_base': fields.float('Base II', required=True,
            digits_compute=dp.get_precision('Account')),
        'ii_value': fields.float('Valor II', required=True,
            digits_compute=dp.get_precision('Account')),
        'ii_iof': fields.float('Valor IOF', required=True,
            digits_compute=dp.get_precision('Account')),
        'ii_customhouse_charges': fields.float('Depesas Atuaneiras',
            required=True, digits_compute=dp.get_precision('Account')),
        'insurance_value': fields.float('Valor do Seguro',
            digits_compute=dp.get_precision('Account')),
        'other_costs_value': fields.float('Outros Custos',
            digits_compute=dp.get_precision('Account')),
        'freight_value': fields.float('Frete',
            digits_compute=dp.get_precision('Account'))
    }
    _defaults = {
        'product_type': 'product',
        'icms_manual': False,
        'icms_origin': '0',
        'icms_base_type': '0',
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
        'icms_st_base_type': '4',
        'issqn_manual': False,
        'issqn_type': 'N',
        'issqn_base': 0.0,
        'issqn_percent': 0.0,
        'issqn_value': 0.0,
        'ipi_manual': False,
        'ipi_type': 'percent',
        'ipi_base': 0.0,
        'ipi_base_other': 0.0,
        'ipi_value': 0.0,
        'ipi_percent': 0.0,
        'pis_manual': False,
        'pis_type': 'percent',
        'pis_base': 0.0,
        'pis_base_other': 0.0,
        'pis_value': 0.0,
        'pis_percent': 0.0,
        'pis_st_type': 'percent',
        'pis_st_base': 0.0,
        'pis_st_percent': 0.0,
        'pis_st_value': 0.0,
        'cofins_manual': False,
        'cofins_type': 'percent',
        'cofins_base': 0.0,
        'cofins_base_other': 0.0,
        'cofins_value': 0.0,
        'cofins_percent': 0.0,
        'cofins_st_type': 'percent',
        'cofins_st_base': 0.0,
        'cofins_st_percent': 0.0,
        'cofins_st_value': 0.0,
        'ii_base': 0.0,
        'ii_value': 0.0,
        'ii_iof': 0.0,
        'ii_customhouse_charges': 0.0
    }

    def _amount_tax_icms(self, cr, uid, tax=None):
        result = {
            'icms_base_type': '0',
            'icms_base': tax.get('total_base', 0.0),
            'icms_base_other': tax.get('total_base_other', 0.0),
            'icms_value': tax.get('amount', 0.0),
            'icms_percent': tax.get('percent', 0.0) * 100,
            'icms_percent_reduction': tax.get('base_reduction') * 100,
        }
        return result

    def _amount_tax_icmsst(self, cr, uid, tax=None):
        result = {
            'icms_st_value': tax.get('amount', 0.0),
            'icms_st_base': tax.get('total_base', 0.0),
            'icms_st_percent': tax.get('icms_st_percent', 0.0) * 100,
            'icms_st_percent_reduction': tax.get('icms_st_percent_reduction', 0.0) * 100,
            'icms_st_mva': tax.get('amount_mva', 0.0) * 100,
            'icms_st_base_other': tax.get('icms_st_base_other', 0.0),
        }
        return result

    def _amount_tax_ipi(self, cr, uid, tax=None):
        result = {
            'ipi_type': tax.get('type'),
            'ipi_base': tax.get('total_base', 0.0),
            'ipi_value': tax.get('amount', 0.0),
            'ipi_percent': tax.get('percent', 0.0) * 100,
        }
        return result

    def _amount_tax_cofins(self, cr, uid, tax=None):
        result = {
            'cofins_base': tax.get('total_base', 0.0),
            'cofins_base_other': tax.get('total_base_other', 0.0),
            'cofins_value': tax.get('amount', 0.0),
            'cofins_percent': tax.get('percent', 0.0) * 100,
        }
        return result

    def _amount_tax_cofinsst(self, cr, uid, tax=None):
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
            'pis_base_other': tax.get('total_base_other', 0.0),
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
            'ii_base': 0.0,
            'ii_value': 0.0,
        }
        return result

    def _amount_tax_issqn(self, cr, uid, tax=False):

        # TODO deixar dinamico a definição do tipo do ISSQN
        # assim como todos os impostos
        issqn_type = 'N'
        if not tax.get('amount'):
            issqn_type = 'I'

        result = {
            'issqn_type': issqn_type,
            'issqn_base': tax.get('total_base', 0.0),
            'issqn_percent': tax.get('percent', 0.0) * 100,
            'issqn_value': tax.get('amount', 0.0),
        }
        return result

    def _get_tax_codes(self, cr, uid, product_id, fiscal_position,
                        taxes, company_id, context=None):

        if not context:
            context = {}

        result = {}

        if fiscal_position.fiscal_category_id.journal_type in ('sale', 'sale_refund'):
            context['type_tax_use'] = 'sale'
        else:
            context['type_tax_use'] = 'purchase'

        context['fiscal_type'] = fiscal_position.fiscal_category_fiscal_type

        tax_codes = self.pool.get('account.fiscal.position').map_tax_code(
            cr, uid, product_id, fiscal_position, company_id,
            taxes, context=context)

        result['icms_cst_id'] = tax_codes.get('icms', False)
        result['ipi_cst_id'] = tax_codes.get('ipi', False)
        result['pis_cst_id'] = tax_codes.get('pis', False)
        result['cofins_cst_id'] = tax_codes.get('cofins', False)
        return result

    def _validate_taxes(self, cr, uid, values, context=None):
        """Verifica se o valor dos campos dos impostos estão sincronizados
        com os impostos do OpenERP"""
        if not context:
            context = {}

        tax_obj = self.pool.get('account.tax')

        if not values.get('product_id') or not values.get('quantity') \
        or not values.get('fiscal_position'):
            return {}

        result = {
            'product_type': 'product',
            'service_type_id': False,
            'fiscal_classification_id': False
        }

        if values.get('partner_id') and values.get('company_id'):
            partner_id = values.get('partner_id')
            company_id = values.get('company_id')
        else:
            if values.get('invoice_id'):
                inv = self.pool.get('account.invoice').read(
                    cr, uid, values.get('invoice_id'),
                    ['partner_id', 'company_id'])

                partner_id = inv.get('partner_id', [False])[0]
                company_id = inv.get('company_id', [False])[0]

        taxes = tax_obj.browse(
            cr, uid, values.get('invoice_line_tax_id')[0][2])
        fiscal_position = self.pool.get('account.fiscal.position').browse(
            cr, uid, values.get('fiscal_position'))

        price_unit = values.get('price_unit', 0.0)
        price = price_unit * (1 - values.get('discount', 0.0) / 100.0)

        taxes_calculed = tax_obj.compute_all(
            cr, uid, taxes, price, values.get('quantity', 0.0),
            values.get('product_id'), partner_id,
            fiscal_position=fiscal_position,
            insurance_value=values.get('insurance_value', 0.0),
            freight_value=values.get('freight_value', 0.0),
            other_costs_value=values.get('other_costs_value', 0.0))

        if values.get('product_id'):
            obj_product = self.pool.get('product.product').browse(
                cr, uid, values.get('product_id'), context=context)
            if obj_product.type == 'service':
                result['product_type'] = 'service'
                result['service_type_id'] = obj_product.service_type_id.id
            else:
                result['product_type'] = 'product'
            if obj_product.property_fiscal_classification:
                result['fiscal_classification_id'] = obj_product.property_fiscal_classification.id

            result['icms_origin'] = obj_product.origin

        for tax in taxes_calculed['taxes']:
            try:
                amount_tax = getattr(
                    self, '_amount_tax_%s' % tax.get('domain', ''))
                result.update(amount_tax(cr, uid, tax))
            except AttributeError:
                # Caso não exista campos especificos dos impostos
                # no documento fiscal, os mesmos são calculados.
                continue

        result.update(self._get_tax_codes(
            cr, uid, values.get('product_id'), fiscal_position,
            values.get('invoice_line_tax_id')[0][2],
            company_id, context=context))
        return result

    def create(self, cr, uid, vals, context=None):
        if not context:
            context = {}
        vals.update(self._validate_taxes(cr, uid, vals, context))
        return super(account_invoice_line, self).create(cr, uid, vals, context)

    def write(self, cr, uid, ids, vals, context=None):
        if not context:
            context = {}
        vals.update(self._validate_taxes(cr, uid, vals, context))
        return super(account_invoice_line, self).write(
            cr, uid, ids, vals, context=context)

    def _fiscal_position_map(self, cr, uid, result, context=None, **kwargs):

        if not context:
            context = {}
        context.update({'use_domain': ('use_invoice', '=', True)})
        kwargs.update({'context': context})
        result['value']['cfop_id'] = False
        obj_fp_rule = self.pool.get('account.fiscal.position.rule')
        result_rule = obj_fp_rule.apply_fiscal_mapping(
            cr, uid, result, kwargs)
        if result['value'].get('fiscal_position', False):
            obj_fp = self.pool.get('account.fiscal.position').browse(
                cr, uid, result['value'].get('fiscal_position', False))
            result_rule['value']['cfop_id'] = obj_fp.cfop_id and obj_fp.cfop_id.id or False
            if kwargs.get('product_id', False):
                obj_product = self.pool.get('product.product').browse(
                cr, uid, kwargs.get('product_id', False), context=context)
                context['fiscal_type'] = obj_product.fiscal_type
                if context.get('type') in ('out_invoice', 'out_refund'):
                    context['type_tax_use'] = 'sale'
                    taxes = obj_product.taxes_id and obj_product.taxes_id or (kwargs.get('account_id', False) and self.pool.get('account.account').browse(cr, uid, kwargs.get('account_id', False), context=context).tax_ids or False)
                else:
                    context['type_tax_use'] = 'purchase'
                    taxes = obj_product.supplier_taxes_id and obj_product.supplier_taxes_id or (kwargs.get('account_id', False) and self.pool.get('account.account').browse(cr, uid, kwargs.get('account_id', False), context=context).tax_ids or False)
                tax_ids = self.pool.get('account.fiscal.position').map_tax(
                    cr, uid, obj_fp, taxes, context)

                result_rule['value']['invoice_line_tax_id'] = tax_ids

                result['value'].update(self._get_tax_codes(
                    cr, uid, kwargs.get('product_id'),
                    obj_fp, tax_ids, kwargs.get('company_id'),
                    context=context))

        return result_rule

    def product_id_change(self, cr, uid, ids, product, uom, qty=0, name='',
                          type='out_invoice', partner_id=False,
                          fposition_id=False, price_unit=False,
                          currency_id=False, context=None, company_id=False,
                          parent_fiscal_category_id=False,
                          parent_fposition_id=False):

        result = super(account_invoice_line, self).product_id_change(
            cr, uid, ids, product, uom, qty, name, type, partner_id,
            fposition_id, price_unit, currency_id, context, company_id)

        fiscal_position = fposition_id or parent_fposition_id or False

        if not parent_fiscal_category_id or not product or not fiscal_position:
            return result
        obj_fp_rule = self.pool.get('account.fiscal.position.rule')
        product_fiscal_category_id = obj_fp_rule.product_fiscal_category_map(
            cr, uid, product, parent_fiscal_category_id)

        if product_fiscal_category_id:
            parent_fiscal_category_id = product_fiscal_category_id

        result['value']['fiscal_category_id'] = parent_fiscal_category_id

        result = self._fiscal_position_map(cr, uid, result, context,
            partner_id=partner_id, partner_invoice_id=partner_id,
            company_id=company_id, product_id=product,
            fiscal_category_id=parent_fiscal_category_id,
            account_id=result['value'].get('account_id'))

        values = {
            'partner_id': partner_id,
            'company_id': company_id,
            'product_id': product,
            'quantity': qty,
            'price_unit': price_unit,
            'fiscal_position': result['value'].get('fiscal_position'),
            'invoice_line_tax_id': [[6, 0, result['value'].get('invoice_line_tax_id')]],
        }
        result['value'].update(self._validate_taxes(cr, uid, values, context))
        return result

    def onchange_fiscal_category_id(self, cr, uid, ids, partner_id,
                                    company_id, product_id, fiscal_category_id,
                                    account_id, context):
        result = {'value': {}}
        return self._fiscal_position_map(
            cr, uid, result, context, partner_id=partner_id,
            partner_invoice_id=partner_id, company_id=company_id,
            fiscal_category_id=fiscal_category_id, product_id=product_id,
            account_id=account_id)

    def onchange_fiscal_position(self, cr, uid, ids, partner_id, company_id,
                                product_id, fiscal_category_id,
                                account_id, context):
        result = {'value': {}}
        return self._fiscal_position_map(
            cr, uid, result, context, partner_id=partner_id,
            partner_invoice_id=partner_id, company_id=company_id,
            fiscal_category_id=fiscal_category_id, product_id=product_id,
            account_id=account_id)

    def onchange_account_id(self, cr, uid, ids, product_id, partner_id,
                            inv_type, fposition_id, account_id=False,
                            context=None, fiscal_category_id=False,
                            company_id=False):

        result = super(account_invoice_line, self).onchange_account_id(
            cr, uid, ids, product_id, partner_id, inv_type, fposition_id,
            account_id)
        return self._fiscal_position_map(
            cr, uid, result, context, partner_id=partner_id,
            partner_invoice_id=partner_id, company_id=company_id,
            fiscal_category_id=fiscal_category_id, product_id=product_id,
            account_id=account_id)

    def uos_id_change(self, cr, uid, ids, product, uom, qty=0, name='',
                    type='out_invoice', partner_id=False, fposition_id=False,
                    price_unit=False, currency_id=False, context=None,
                    company_id=None, fiscal_category_id=False):

        result = super(account_invoice_line, self).uos_id_change(
            cr, uid, ids, product, uom, qty, name, type, partner_id,
            fposition_id, price_unit, currency_id, context, company_id)
        return self._fiscal_position_map(
            cr, uid, result, context, partner_id=partner_id,
            partner_invoice_id=partner_id, company_id=company_id,
            fiscal_category_id=fiscal_category_id, product_id=product,
            account_id=False)


class account_invoice_tax(orm.Model):
    _inherit = "account.invoice.tax"

    def compute(self, cr, uid, invoice_id, context=None):
        tax_grouped = {}
        tax_obj = self.pool.get('account.tax')
        cur_obj = self.pool.get('res.currency')
        inv = self.pool.get('account.invoice').browse(
            cr, uid, invoice_id, context=context)
        cur = inv.currency_id
        currenty_date = time.strftime('%Y-%m-%d')
        company_currency = inv.company_id.currency_id.id

        for line in inv.invoice_line:
            for tax in tax_obj.compute_all(
                cr, uid, line.invoice_line_tax_id,
                (line.price_unit * (1 - (line.discount or 0.0) / 100.0)),
                line.quantity, line.product_id, inv.partner_id,
                fiscal_position=line.fiscal_position,
               insurance_value=line.insurance_value,
                freight_value=line.freight_value,
                other_costs_value=line.other_costs_value)['taxes']:
                val = {}
                val['invoice_id'] = inv.id
                val['name'] = tax['name']
                val['amount'] = tax['amount']
                val['manual'] = False
                val['sequence'] = tax['sequence']
                val['base'] = tax.get('total_base', 0.0)

                if inv.type in ('out_invoice', 'in_invoice'):
                    val['base_code_id'] = tax['base_code_id']
                    val['tax_code_id'] = tax['tax_code_id']
                    val['base_amount'] = cur_obj.compute(cr, uid,
                        inv.currency_id.id, company_currency,
                        val['base'] * tax['base_sign'],
                        context={'date': inv.date_invoice or currenty_date},
                        round=False)
                    val['tax_amount'] = cur_obj.compute(
                        cr, uid, inv.currency_id.id, company_currency,
                        val['amount'] * tax['tax_sign'],
                        context={'date': inv.date_invoice or currenty_date},
                        round=False)
                    val['account_id'] = tax['account_collected_id'] or line.account_id.id
                    val['account_analytic_id'] = tax['account_analytic_collected_id']
                else:
                    val['base_code_id'] = tax['ref_base_code_id']
                    val['tax_code_id'] = tax['ref_tax_code_id']
                    val['base_amount'] = cur_obj.compute(
                        cr, uid, inv.currency_id.id, company_currency,
                        val['base'] * tax['ref_base_sign'],
                        context={'date': inv.date_invoice or currenty_date},
                        round=False)
                    val['tax_amount'] = cur_obj.compute(
                        cr, uid, inv.currency_id.id,
                        company_currency, val['amount'] * tax['ref_tax_sign'],
                        context={'date': inv.date_invoice or currenty_date},
                        round=False)
                    val['account_id'] = tax['account_paid_id'] or line.account_id.id
                    val['account_analytic_id'] = tax['account_analytic_paid_id']

                key = (val['tax_code_id'], val['base_code_id'], val['account_id'], val['account_analytic_id'])
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
