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

from openerp import models, api, fields, _
from openerp import netsvc
from openerp.osv import orm
import openerp.addons.decimal_precision as dp

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


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'


    @api.one
    @api.depends(
        'move_id.line_id'
    )
    def _get_receivable_lines(self):
        if self.move_id:
            data_lines = [x for x in self.move_id.line_id if (
                x.account_id.id == self.account_id.id
                and x.account_id.type in ('receivable', 'payable')
                and self.journal_id.revenue_expense)]
            New_ids = []
            for line in data_lines:
                New_ids.append(line.id)
                New_ids.sort()
            self.move_line_receivable_id = New_ids

    def _default_fiscal_document(self):
        fiscal_document = self.env.user.company_id.service_invoice_id
        return fiscal_document

    def _default_fiscal_document_serie(self):
        fiscal_document_serie = self.env.user.company_id.document_serie_service_id
        return fiscal_document_serie

    issuer = fields.Selection(
        [('0', u'Emissão própria'),
        ('1', 'Terceiros')], string='Emitente', readonly=True,
        states={'draft': [('readonly', False)]}, default=0)
    internal_number = fields.Char(
        string='Invoice Number', size=32, readonly=True,
        states={'draft': [('readonly', False)]},
        help="""Unique number of the invoice, computed
            automatically when the invoice is created.""")
    fiscal_type = fields.Selection(
        PRODUCT_FISCAL_TYPE, string='Tipo Fiscal', required=True,
        default=PRODUCT_FISCAL_TYPE_DEFAULT)
    vendor_serie = fields.Char(
        string=u'Série NF Entrada', size=12, readonly=True,
        states={'draft': [('readonly', False)]},
        help=u"Série do número da Nota Fiscal do Fornecedor")
    move_line_receivable_id = fields.Many2many(
        'account.move.line', compute='_get_receivable_lines',
        method=True, string='Entry Lines')
    document_serie_id = fields.Many2one(
        'l10n_br_account.document.serie', string=u'Série',
        domain="[('fiscal_document_id', '=', fiscal_document_id),\
        ('company_id','=',company_id)]", readonly=True,
        states={'draft': [('readonly', False)]}, default=_default_fiscal_document_serie)
    fiscal_document_id = fields.Many2one(
        'l10n_br_account.fiscal.document', string='Documento', readonly=True,
        states={'draft': [('readonly', False)]}, default=_default_fiscal_document)
    fiscal_document_electronic = fields.Boolean(
        related='fiscal_document_id.electronic', type='boolean', readonly=True,
        store=True, string='Electronic')
    fiscal_category_id = fields.Many2one(
        'l10n_br_account.fiscal.category', string='Categoria Fiscal',
        readonly=True, states={'draft': [('readonly', False)]})
    fiscal_position = fields.Many2one(
        'account.fiscal.position', string='Fiscal Position', readonly=True,
        states={'draft': [('readonly', False)]},
        domain="[('fiscal_category_id','=',fiscal_category_id)]")
    account_document_event_ids = fields.One2many(
        'l10n_br_account.document_event', 'document_event_ids',
        string=u'Eventos')
    fiscal_comment = fields.Text(string=u'Observação Fiscal')

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
            'nfe_protocol_number': False,
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
                        _(u"O número: %s da série: %s, esta inutilizado") % (
                            sequence_read['number_next'],
                            inv.document_serie_id.name))

                seq_no = sequence.get_id(cr, uid, inv.document_serie_id.internal_sequence_id.id, context=context)
                self.write(cr, uid, inv.id, {'ref': seq_no, 'internal_number': seq_no})
        return True

    @api.one
    def action_number(self):
        # #TODO: not correct fix but required a frech values before reading it.
        # self.write(cr, uid, ids, {}) #removed: luisfelipemileo

        inv_id = self.id
        move_id = self.move_id and self.move_id.id or False
        ref = self.internal_number or self.reference or ''

        self._cr.execute('UPDATE account_move SET ref=%s '
            'WHERE id=%s AND (ref is null OR ref = \'\')',
                (ref, move_id))
        self._cr.execute('UPDATE account_move_line SET ref=%s '
            'WHERE move_id=%s AND (ref is null OR ref = \'\')',
            (ref, move_id))
        self._cr.execute('UPDATE account_analytic_line SET ref=%s '
            'FROM account_move_line '
            'WHERE account_move_line.move_id = %s '
            'AND account_analytic_line.move_id = account_move_line.id',
            (ref, move_id))

        #TODO Usar OpenChatter para gerar um registro que a fatura foi validada.
        #for inv_id, name in self.name_get(cr, uid, [inv_id]):
        #    ctx = context.copy()
        #    if obj_inv.type in ('out_invoice', 'out_refund'):
        #        ctx = self.get_log_context(cr, uid, context=ctx)
        #    message = _('Invoice ') + " '" + name + "' " + _("is validated.")
        #    self.log(cr, uid, inv_id, message, context=ctx)

    @api.multi
    def finalize_invoice_move_lines(self, move_lines):
        """finalize_invoice_move_lines(cr, uid, invoice, move_lines) -> move_lines
        Hook method to be overridden in additional modules to verify and possibly alter the
        move lines to be created by an invoice, for special cases.
        :param invoice_browse: browsable record of the invoice that is generating the move lines
        :param move_lines: list of dictionaries with the account.move.lines (as for create())
        :return: the (possibly updated) final move_lines to create for this invoice
        """        
        move_lines = super(AccountInvoice, self).finalize_invoice_move_lines(move_lines)
        cont=1
        result = []
        for move_line in move_lines:
            if (move_line[2]['debit'] or move_line[2]['credit']):
                if (move_line[2]['account_id'] == self.account_id.id):
                    move_line[2]['name'] = '%s/%s' % ( self.internal_number, cont)
                    cont +=1
                result.append(move_line)
        return result

    @api.model
    def _fiscal_position_map(self, result, context=None, **kwargs):

        if not context:
            context = {}
        context.update({'use_domain': ('use_invoice', '=', True)})
        kwargs.update({'context': context})

        if not kwargs.get('fiscal_category_id', False):
            return result
        obj_company = self.env['res.company'].browse(kwargs.get('company_id',
                                                                False))
        obj_fcategory = self.env['l10n_br_account.fiscal.category']
        fcategory = obj_fcategory.browse(kwargs.get('fiscal_category_id'))
        result['value']['journal_id'] = fcategory.property_journal and \
            fcategory.property_journal.id or False
        if not result['value'].get('journal_id', False):
            raise orm.except_orm(
                _(u'Nenhum Diário !'),
                _(u"Categoria fiscal: '%s', não tem um diário contábil para a \
                empresa %s") % (fcategory.name, obj_company.name))

        obj_fp_rule = self.env['account.fiscal.position.rule']
        return obj_fp_rule.apply_fiscal_mapping(result, **kwargs)

    @api.multi
    def onchange_partner_id(self, type, partner_id,
                            date_invoice=False, payment_term=False,
                            partner_bank_id=False, company_id=False):

        fiscal_category_id = self._context.get('fiscal_category_id')

        result = super(AccountInvoice, self).onchange_partner_id(
            type, partner_id, date_invoice, payment_term,
            partner_bank_id, company_id)

        return self._fiscal_position_map(
            result, False, partner_id=partner_id,
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

    #TODO: Fix this method to avoid erros with document_serie_product_ids
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


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'


    @api.one
    @api.depends('price_unit', 'discount', 'invoice_line_tax_id', 'quantity',
                 'product_id', 'invoice_id.partner_id',
                 'invoice_id.currency_id', 'fiscal_position')
    def _compute_price(self):
        price = self.price_unit * (1 - (self.discount or 0.0) / 100.0)
        taxes = self.invoice_line_tax_id.compute_all(
            price, self.quantity, product=self.product_id, partner=self.invoice_id.partner_id,
            fiscal_position=self.fiscal_position)
        self.price_subtotal = taxes['total'] - taxes['total_tax_discount']
        self.price_total = taxes['total']
        if self.invoice_id:
            self.price_subtotal = self.invoice_id.currency_id.round(self.price_subtotal)
            self.price_total = self.invoice_id.currency_id.round(self.price_total)

    fiscal_category_id = fields.Many2one(
        'l10n_br_account.fiscal.category', string='Categoria')
    fiscal_position = fields.Many2one(
        'account.fiscal.position', string=u'Posição Fiscal',
        domain="[('fiscal_category_id','=',fiscal_category_id)]")
    price_total = fields.Float(
        compute='_compute_price', method=True, string='Total',
        digits_compute=dp.get_precision('Account'),
        store=True, multi='all')

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

            # product_ids = eview.xpath("//field[@name='product_id']")
            # for product_id in product_ids:
            #     product_id.set('domain', "[('fiscal_type', '=', '%s')]" % (
            #         context.get('fiscal_type', 'service')))

            result['arch'] = etree.tostring(eview)

        return result

    @api.model
    def _fiscal_position_map(self, result, context=None, **kwargs):

        context = dict(context or self._context)
        context.update({'use_domain': ('use_invoice', '=', True)})
        kwargs.update({'context': context})
        result['value']['cfop_id'] = False

        obj_fp_rule = self.env['account.fiscal.position.rule']
        result_rule = obj_fp_rule.apply_fiscal_mapping(
            result, **kwargs)
        if result['value'].get('fiscal_position', False):
            obj_fp = self.env['account.fiscal.position'].browse(
                result['value'].get('fiscal_position', False))
            result_rule['value'][
                'cfop_id'] = obj_fp.cfop_id and obj_fp.cfop_id.id or False
            if kwargs.get('product_id', False):
                obj_product = self.env['product.product'].browse(
                    kwargs.get('product_id', False))
                context['fiscal_type'] = obj_product.fiscal_type
                if context.get('type') in ('out_invoice', 'out_refund'):
                    context['type_tax_use'] = 'sale'
                    taxes = obj_product.taxes_id and obj_product.taxes_id or (
                        kwargs.get('account_id', False) and self.env[
                            'account.account'].browse(
                            kwargs.get('account_id', False)).tax_ids or False)
                else:
                    context['type_tax_use'] = 'purchase'
                    taxes = obj_product.supplier_taxes_id and \
                        obj_product.supplier_taxes_id or (
                            kwargs.get('account_id', False) and self.env[
                                'account.account'].browse(
                                kwargs.get('account_id',
                                           False)).tax_ids or False)
                tax_ids = obj_fp.map_tax(taxes).ids
                result_rule['value']['invoice_line_tax_id'] = tax_ids
                result['value'].update(
                    self._get_tax_codes(kwargs.get('product_id'), obj_fp,
                                        tax_ids, kwargs.get('company_id')))
        return result_rule

    @api.multi
    def product_id_change(self, product, uom, qty=0, name='',
                          type='out_invoice', partner_id=False,
                          fposition_id=False, price_unit=False,
                          currency_id=False, context=None, company_id=False,
                          parent_fiscal_category_id=False,
                          parent_fposition_id=False):

        result = super(AccountInvoiceLine, self).product_id_change(
            product, uom, qty=qty, name=name, type=type, partner_id=partner_id,
            fposition_id=fposition_id, price_unit=price_unit, currency_id=currency_id,
            company_id=company_id)
        fiscal_position = fposition_id or parent_fposition_id or False

        if not parent_fiscal_category_id or not product or not fiscal_position:
            return result
        obj_fp_rule = self.env['account.fiscal.position.rule']
        product_fiscal_category_id = obj_fp_rule.product_fiscal_category_map(
            product, parent_fiscal_category_id)

        if product_fiscal_category_id:
            parent_fiscal_category_id = product_fiscal_category_id

        result['value']['fiscal_category_id'] = parent_fiscal_category_id

        result = self._fiscal_position_map(result, context,
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
        result['value'].update(self._validate_taxes(values))
        return result

    @api.multi
    def onchange_fiscal_category_id(self, partner_id,
                                    company_id, product_id, fiscal_category_id,
                                    account_id, context):
        result = {'value': {}}
        return self._fiscal_position_map(
            result, context, partner_id=partner_id,
            partner_invoice_id=partner_id, company_id=company_id,
            fiscal_category_id=fiscal_category_id, product_id=product_id,
            account_id=account_id)

    @api.multi
    def onchange_fiscal_position(self, partner_id, company_id,
                                product_id, fiscal_category_id,
                                account_id, context):
        result = {'value': {}}
        return self._fiscal_position_map(
            result, context, partner_id=partner_id,
            partner_invoice_id=partner_id, company_id=company_id,
            fiscal_category_id=fiscal_category_id, product_id=product_id,
            account_id=account_id)

    @api.multi
    def onchange_account_id(self, product_id, partner_id,
                            inv_type, fposition_id, account_id=False,
                            context=None, fiscal_category_id=False,
                            company_id=False):
        result = super(AccountInvoiceLine, self).onchange_account_id(
            product_id, partner_id, inv_type, fposition_id, account_id)
        return self._fiscal_position_map(result, context, partner_id=partner_id,
            partner_invoice_id=partner_id, company_id=company_id,
            fiscal_category_id=fiscal_category_id, product_id=product_id,
            account_id=account_id)
        return result

    @api.multi
    def uos_id_change(self, product, uom, qty=0, name='',
                    type='out_invoice', partner_id=False, fposition_id=False,
                    price_unit=False, currency_id=False, context=None,
                    company_id=None, fiscal_category_id=False):

        result = super(AccountInvoiceLine, self).uos_id_change(
            product, uom, qty=qty, name=name, type=type, partner_id=partner_id,
            fposition_id=fposition_id, price_unit=price_unit, currency_id=currency_id, 
            company_id=company_id)
        # return self._fiscal_position_map(
        #     self._cr, self._uid, result, context, partner_id=partner_id,
        #     partner_invoice_id=partner_id, company_id=company_id,
        #     fiscal_category_id=fiscal_category_id, product_id=product,
        #     account_id=False)
        return result