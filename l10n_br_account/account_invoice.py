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

from openerp import netsvc
from openerp.osv import orm, fields
from openerp.addons import decimal_precision as dp
from openerp.tools.translate import _

from .l10n_br_account import PRODUCT_FISCAL_TYPE, PRODUCT_FISCAL_TYPE_DEFAULT

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


class AccountInvoice(orm.Model):
    _inherit = 'account.invoice'

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
        'issuer': fields.selection(
            [('0', u'Emissão própria'),
            ('1', 'Terceiros')], 'Emitente', readonly=True,
            states={'draft': [('readonly', False)]}),
        'internal_number': fields.char(
            'Invoice Number', size=32, readonly=True,
            states={'draft': [('readonly', False)]},
            help="""Unique number of the invoice, computed
                automatically when the invoice is created."""),
        'fiscal_type': fields.selection(
            PRODUCT_FISCAL_TYPE, 'Tipo Fiscal', required=True),
        'vendor_serie': fields.char(
            'Série NF Entrada', size=12, readonly=True,
            states={'draft': [('readonly', False)]},
            help=u"Série do número da Nota Fiscal do Fornecedor"),
        'move_line_receivable_id': fields.function(
            _get_receivable_lines, method=True, type='many2many',
            relation='account.move.line', string='Entry Lines'),
        'document_serie_id': fields.many2one(
            'l10n_br_account.document.serie', u'Série',
            domain="[('fiscal_document_id','=',fiscal_document_id),\
            ('company_id','=',company_id)]", readonly=True,
            states={'draft': [('readonly', False)]}),
        'fiscal_document_id': fields.many2one(
            'l10n_br_account.fiscal.document', 'Documento', readonly=True,
            states={'draft': [('readonly', False)]}),
        'fiscal_document_electronic': fields.related(
            'fiscal_document_id', 'electronic', type='boolean', readonly=True,
            relation='l10n_br_account.fiscal.document', store=True,
            string='Electronic'),
        'fiscal_category_id': fields.many2one(
            'l10n_br_account.fiscal.category', 'Categoria Fiscal',
            readonly=True, states={'draft': [('readonly', False)]}),
        'fiscal_position': fields.many2one(
            'account.fiscal.position', 'Fiscal Position', readonly=True,
            states={'draft': [('readonly', False)]},
            domain="[('fiscal_category_id','=',fiscal_category_id)]"),
        'account_document_event_ids': fields.one2many(
            'l10n_br_account.document_event', 'document_event_ids',
            u'Eventos'),
        'fiscal_comment': fields.text('Observação Fiscal'),
    }

    def _default_fiscal_document(self, cr, uid, context):
        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        fiscal_document = self.pool.get('res.company').read(
            cr, uid, user.company_id.id, ['service_invoice_id'],
            context=context)['service_invoice_id']

        return fiscal_document and fiscal_document[0] or False

    def _default_fiscal_document_serie(self, cr, uid, context):
        fiscal_document_serie = False
        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        company = self.pool.get('res.company').browse(
            cr, uid, user.company_id.id, context=context)

        fiscal_document_serie = company.document_serie_service_id and \
            company.document_serie_service_id.id or False

        return fiscal_document_serie

    _defaults = {
        'issuer': '0',
        'fiscal_type': PRODUCT_FISCAL_TYPE_DEFAULT,
        'fiscal_document_id': _default_fiscal_document,
        'document_serie_id': _default_fiscal_document_serie,
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

    #TODO - Melhorar esse método!
    def fields_view_get(self, cr, uid, view_id=None, view_type=False,
                        context=None, toolbar=False, submenu=False):
        result = super(AccountInvoice, self).fields_view_get(
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

                fiscal_categories = eview.xpath(
                    "//field[@name='fiscal_category_id']")
                for fiscal_category_id in fiscal_categories:
                    fiscal_category_id.set(
                        'domain',
                        """[('fiscal_type', '=', '%s'), ('type', '=', '%s'),
                        ('state', '=', 'approved'),
                        ('journal_type', '=', '%s')]"""
                        % (context.get('fiscal_type', 'product'),
                            OPERATION_TYPE[context['type']],
                            JOURNAL_TYPE[context['type']]))
                    fiscal_category_id.set('required', '1')

                document_series = eview.xpath(
                    "//field[@name='document_serie_id']")
                for document_serie_id in document_series:
                    document_serie_id.set(
                        'domain', "[('fiscal_type', '=', '%s')]"
                        % (context.get('fiscal_type', 'product')))

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
            'account_document_event_ids': False,
        })
        return super(AccountInvoice, self).copy(cr, uid, id, default, context)

    def action_internal_number(self, cr, uid, ids, context=None):
        if context is None:
            context = {}

        for inv in self.browse(cr, uid, ids):
            if inv.issuer == '0':
                sequence = self.pool.get('ir.sequence')
                sequence_read = sequence.read(
                    cr, uid, inv.document_serie_id.internal_sequence_id.id,
                    ['number_next'])
                invalid_number = self.pool.get(
                    'l10n_br_account.invoice.invalid.number').search(
                        cr, uid, [
                        ('number_start', '<=', sequence_read['number_next']),
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
        result = super(AccountInvoice, self).action_move_create(
            cr, uid, ids, *args)
        for inv in self.browse(cr, uid, ids):
            if inv.move_id:
                self.pool.get('account.move').write(
                    cr, uid, [inv.move_id.id], {'ref': inv.internal_number})
                for move_line in inv.move_id.line_id:
                    self.pool.get('account.move.line').write(
                        cr, uid, [move_line.id], {'ref': inv.internal_number})
                move_lines = [x for x in inv.move_id.line_id if x.account_id.id == inv.account_id.id and x.account_id.type in ('receivable', 'payable')]
                i = len(move_lines)
                for move_line in move_lines:
                    move_line_name = '%s/%s' % (inv.internal_number, i)
                    self.pool.get('account.move.line').write(
                        cr, uid, [move_line.id], {'name': move_line_name})
                    i -= 1
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
        return obj_fp_rule.apply_fiscal_mapping(cr, uid, result, **kwargs)

    def onchange_partner_id(self, cr, uid, ids, type, partner_id,
                            date_invoice=False, payment_term=False,
                            partner_bank_id=False, company_id=False,
                            fiscal_category_id=False):

        result = super(AccountInvoice, self).onchange_partner_id(
            cr, uid, ids, type, partner_id, date_invoice, payment_term,
            partner_bank_id, company_id)

        return self._fiscal_position_map(
            cr, uid, result, False, partner_id=partner_id,
            partner_invoice_id=partner_id, company_id=company_id,
            fiscal_category_id=fiscal_category_id)

    def onchange_company_id(self, cr, uid, ids, company_id, partner_id, type,
                            invoice_line, currency_id,
                            fiscal_category_id=False):

        result = super(AccountInvoice, self).onchange_company_id(
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
            serie = company.document_serie_service_id and \
            company.document_serie_service_id.id or False
            result['value']['document_serie_id'] = serie

        return result


class AccountInvoiceLine(orm.Model):
    _inherit = 'account.invoice.line'

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
                fiscal_position=line.fiscal_position)

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
        'price_total': fields.function(
            _amount_line, method=True, string='Total', type="float",
            digits_compute=dp.get_precision('Account'),
            store=True, multi='all'),
    }

    def fields_view_get(self, cr, uid, view_id=None, view_type=False,
                        context=None, toolbar=False, submenu=False):

        result = super(AccountInvoiceLine, self).fields_view_get(
            cr, uid, view_id=view_id, view_type=view_type, context=context,
            toolbar=toolbar, submenu=submenu)

        if context is None:
            context = {}

        if view_type == 'form':
            eview = etree.fromstring(result['arch'])

            if 'type' in context.keys():
                fiscal_categories = eview.xpath("//field[@name='fiscal_category_id']")
                for fiscal_category_id in fiscal_categories:
                    fiscal_category_id.set(
                        'domain', """[('type', '=', '%s'),
                        ('journal_type', '=', '%s')]"""
                        % (OPERATION_TYPE[context['type']],
                        JOURNAL_TYPE[context['type']]))
                    fiscal_category_id.set('required', '1')

            product_ids = eview.xpath("//field[@name='product_id']")
            for product_id in product_ids:
                product_id.set('domain', "[('fiscal_type', '=', '%s')]" % (
                    context.get('fiscal_type', 'service')))

            result['arch'] = etree.tostring(eview)

        return result

    def _fiscal_position_map(self, cr, uid, result, context=None, **kwargs):

        if not context:
            context = {}
        context.update({'use_domain': ('use_invoice', '=', True)})
        kwargs.update({'context': context})
        result['value']['cfop_id'] = False
        obj_fp_rule = self.pool.get('account.fiscal.position.rule')
        result_rule = obj_fp_rule.apply_fiscal_mapping(
            cr, uid, result, **kwargs)
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

        result = super(AccountInvoiceLine, self).product_id_change(
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

        result = super(AccountInvoiceLine, self).onchange_account_id(
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

        result = super(AccountInvoiceLine, self).uos_id_change(
            cr, uid, ids, product, uom, qty, name, type, partner_id,
            fposition_id, price_unit, currency_id, context, company_id)
        return self._fiscal_position_map(
            cr, uid, result, context, partner_id=partner_id,
            partner_invoice_id=partner_id, company_id=company_id,
            fiscal_category_id=fiscal_category_id, product_id=product,
            account_id=False)
