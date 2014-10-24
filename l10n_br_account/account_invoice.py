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

from openerp import models, fields, api, _
from openerp.addons import decimal_precision as dp
from openerp.exceptions import except_orm, Warning

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
        'move_id.line_id.reconcile_id.line_id',
        'move_id.line_id.reconcile_partial_id.line_partial_ids',
    )
    def _compute_receivables(self):
        lines = self.env['account.move.line']
        for line in self.move_id.line_id:
            if line.account_id.id == self.account_id.id and \
                line.account_id.type in ('receivable', 'payable') and \
                self.journal_id.revenue_expense:
                lines |= line
        self.move_line_receivable_id = (lines).sorted()

    @api.model
    def _default_fiscal_document(self):
        company = self.env['res.company'].browse(self.env.user.company_id.id)
        return company.service_invoice_id

    @api.model
    def _default_fiscal_document_serie(self):
        company = self.env['res.company'].browse(self.env.user.company_id.id)
        return company.document_serie_service_id

    issuer = fields.Selection(
        [('0', u'Emissão própria'), ('1', 'Terceiros')], 'Emitente',
        default='0', readonly=True, states={'draft': [('readonly', False)]})
    internal_number = fields.Char(
        'Invoice Number', size=32, readonly=True,
        states={'draft': [('readonly', False)]},
        help="""Unique number of the invoice, computed
            automatically when the invoice is created.""")
    fiscal_type = fields.Selection(
        PRODUCT_FISCAL_TYPE, 'Tipo Fiscal', required=True,
        default=PRODUCT_FISCAL_TYPE_DEFAULT)
    vendor_serie = fields.Char(
        'Série NF Entrada', size=12, readonly=True,
        states={'draft': [('readonly', False)]},
        help=u"Série do número da Nota Fiscal do Fornecedor")
    move_line_receivable_id = fields.Many2many(
        'account.move.line', string='Receivables',
        compute='_compute_receivables')
    fiscal_document_id = fields.Many2one(
        'l10n_br_account.fiscal.document', 'Documento', readonly=True,
        states={'draft': [('readonly', False)]},
        default=_default_fiscal_document)
    fiscal_document_electronic = fields.Boolean(
        related='fiscal_document_id.electronic')
    document_serie_id = fields.Many2one(
        'l10n_br_account.document.serie', u'Série',
        domain="[('fiscal_document_id', '=', fiscal_document_id),\
        ('company_id','=',company_id)]", readonly=True,
        states={'draft': [('readonly', False)]},
        default=_default_fiscal_document_serie)
    fiscal_category_id = fields.Many2one(
        'l10n_br_account.fiscal.category', 'Categoria Fiscal',
        readonly=True, states={'draft': [('readonly', False)]})
    fiscal_position = fields.Many2one(
        'account.fiscal.position', 'Fiscal Position', readonly=True,
        states={'draft': [('readonly', False)]},
        domain="[('fiscal_category_id','=',fiscal_category_id)]")
    account_document_event_ids = fields.One2many(
        'l10n_br_account.document_event', 'document_event_ids',
        u'Eventos')
    fiscal_comment = fields.Text(u'Observação Fiscal')

    @api.one
    @api.constrains('number')
    def _check_invoice_number(self):
        domain = []
        if self.number:
            fiscal_document = self.fiscal_document_id and self.fiscal_document_id.id or False
            domain.extend([('internal_number', '=', self.number),
                           ('fiscal_type', '=', self.fiscal_type),
                           ('fiscal_document_id', '=', fiscal_document)
                           ])
            if self.issuer == '0':
                domain.extend([
                    ('company_id', '=', self.company_id.id),
                    ('internal_number', '=', self.number),
                    ('fiscal_document_id', '=', self.fiscal_document_id.id),
                    ('issuer', '=', '0')])
            else:
                domain.extend([
                    ('partner_id', '=', self.partner_id.id),
                    ('vendor_serie', '=', self.vendor_serie),
                    ('issuer', '=', '1')])

            invoices = self.env['account.invoice'].search(domain)
            if len(invoices) > 1:
                raise Warning(u'Não é possível registrar documentos fiscais com números repetidos.')

    _sql_constraints = [
        ('number_uniq', 'unique(number, company_id, journal_id, type, partner_id)',
            'Invoice Number must be unique per Company!'),
    ]

    #TODO não foi migrado por causa do bug github.com/odoo/odoo/issues/1711
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

    @api.multi
    def action_number(self):
        #TODO: not correct fix but required a fresh values before reading it.
        self.write({})

        for invoice in self:
            if invoice.issuer == '0':
                sequence_obj = self.env['ir.sequence']
                sequence = sequence_obj.browse(
                    invoice.document_serie_id.internal_sequence_id.id)
                invalid_number = self.env[
                    'l10n_br_account.invoice.invalid.number'].search([
                        ('number_start', '<=', sequence.number_next),
                        ('number_end', '>=', sequence.number_next),
                        ('state', '=', 'done')])

                if invalid_number:
                    raise except_orm(
                        _(u'Número Inválido !'),
                        _("O número: %s da série: %s, esta inutilizado") % (
                            sequence.number_next,
                            invoice.document_serie_id.name))

                seq_number = sequence_obj.get_id(
                    invoice.document_serie_id.internal_sequence_id.id)
                self.write({'internal_number': seq_number, 'number': seq_number})
        return True

    # TODO Talvez este metodo substitui o metodo action_move_create
    @api.multi
    def finalize_invoice_move_lines(self, move_lines):
        """ finalize_invoice_move_lines(move_lines) -> move_lines

            Hook method to be overridden in additional modules to verify and
            possibly alter the move lines to be created by an invoice, for
            special cases.
            :param move_lines: list of dictionaries with the account.move.lines (as for create())
            :return: the (possibly updated) final move_lines to create for this invoice
        """
        move_lines = super(AccountInvoice, self).finalize_invoice_move_lines(move_lines)
        cont=1
        result = []
        for move_line in move_lines:
            if (move_line[2]['debit'] or move_line[2]['credit']):
                if (move_line[2]['account_id'] == invoice_browse.account_id.id):
                    move_line[2]['name'] = '%s/%s' % (self.internal_number, cont)
                    cont +=1
                result.append(move_line)
        return result

    def _fiscal_position_map(self, result, **kwargs):
        ctx = dict(self._context)
        ctx.update({'use_domain': ('use_invoice', '=', True)})

        if not ctx.get('fiscal_category_id'):
            return result

        kwargs['fiscal_category_id'] = ctx.get('fiscal_category_id')

        company = self.env['res.company'].browse(kwargs.get('company_id'))

        fcategory = self.env['l10n_br_account.fiscal.category'].browse(
            kwargs.get('fiscal_category_id'))
        result['value']['journal_id'] = fcategory.property_journal.id
        if not result['value'].get('journal_id', False):
            raise except_orm(
                _('Nenhum Diário !'),
                _("Categoria fiscal: '%s', não tem um diário contábil para a \
                empresa %s") % (fcategory.name, company.name))
        return self.env['account.fiscal.position.rule'].with_context(
            ctx).apply_fiscal_mapping(result, **kwargs)

    @api.multi
    def onchange_fiscal_category_id(self, partner_address_id,
                                    partner_id, company_id,
                                    fiscal_category_id):
        #TODO Deixar em branco a posição fiscal se não achar a regra
        result = {'value': {'fiscal_position': None}}
        if fiscal_category_id:
            fiscal_category = self.env[
                'l10n_br_account.fiscal.category'].browse(fiscal_category_id)
            #TODO CASO NAO TENHA DIARIO EXIBIR UMA MENSAGEM
            if fiscal_category.property_journal:
                result['value']['journal_id'] = fiscal_category.property_journal.id
        return self._fiscal_position_map(
            result, partner_id=partner_id,
            partner_invoice_id=partner_address_id, company_id=company_id,
            fiscal_category_id=fiscal_category_id)

    @api.multi
    def onchange_fiscal_document_id(self, fiscal_document_id,
                                    company_id, issuer, fiscal_type):
        result = {'value': {'document_serie_id': False}}
        company = self.env['res.company'].browse(company_id)

        if issuer == '0':
            serie = company.document_serie_service_id and \
            company.document_serie_service_id.id or False
            result['value']['document_serie_id'] = serie

        return result


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    @api.one
    @api.depends('price_unit', 'discount', 'invoice_line_tax_id',
                 'quantity', 'product_id', 'invoice_id.partner_id',
                 'invoice_id.currency_id')
    def _compute_price(self):
        price = self.price_unit * (1 - (self.discount or 0.0) / 100.0)
        taxes = self.invoice_line_tax_id.compute_all(
            price, self.quantity, product=self.product_id,
            partner=self.invoice_id.partner_id,
            fiscal_position=self.fiscal_position)
        self.price_subtotal = taxes['total'] - taxes['total_tax_discount']
        self.price_total = taxes['total']
        if self.invoice_id:
            self.price_subtotal = self.invoice_id.currency_id.round(
                self.price_subtotal)
            self.price_total = self.invoice_id.currency_id.round(
                self.price_total)

    invoice_line_tax_id = fields.Many2many(
        'account.tax', 'account_invoice_line_tax', 'invoice_line_id',
        'tax_id', string='Taxes', domain=[('parent_id', '=', False)])
    fiscal_category_id = fields.Many2one(
        'l10n_br_account.fiscal.category', 'Categoria Fiscal')
    fiscal_position = fields.Many2one(
        'account.fiscal.position', u'Posição Fiscal',
        domain="[('fiscal_category_id', '=', fiscal_category_id)]")
    price_total = fields.Float(
        string='Amount', store=True, digits=dp.get_precision('Account'),
        readonly=True, compute='_compute_price')

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

    @api.model
    def _fiscal_position_map(self, result, **kwargs):
        ctx = dict(self.env.context)
        ctx.update({'use_domain': ('use_invoice', '=', True)})
        #result['value']['cfop_id'] = None

        result_rule = self.env[
            'account.fiscal.position.rule'].with_context(
                ctx).apply_fiscal_mapping(result, **kwargs)
        if result_rule.get('fiscal_position'):
            obj_fp = self.pool.get('account.fiscal.position').browse(
                result_rule.get('fiscal_position', False))
            if kwargs.get('product_id', False):
                obj_product = self.env['product.product'].browse(
                kwargs.get('product_id', False))
                ctx['fiscal_type'] = obj_product.fiscal_type
                if ctx.get('type') in ('out_invoice', 'out_refund'):
                    ctx['type_tax_use'] = 'sale'
                    taxes = obj_product.taxes_id and obj_product.taxes_id or (kwargs.get('account_id', False) and self.pool.get('account.account').browse(kwargs.get('account_id', False)).tax_ids or False)
                else:
                    ctx['type_tax_use'] = 'purchase'
                    taxes = obj_product.supplier_taxes_id and obj_product.supplier_taxes_id or (kwargs.get('account_id', False) and self.pool.get('account.account').browse(kwargs.get('account_id', False)).tax_ids or False)
                tax_ids = self.env['account.fiscal.position'].with_context(
                    ctx).map_tax(obj_fp, taxes)

                result_rule['value']['invoice_line_tax_id'] = tax_ids

                result['value'].update(self._get_tax_codes(
                    kwargs.get('product_id'),
                    obj_fp, tax_ids, kwargs.get('company_id')))

        return result_rule

    @api.multi
    def product_id_change(self, product, uom_id, qty=0, name='',
                        type='out_invoice', partner_id=False,
                        fposition_id=False, price_unit=False,
                        currency_id=False, company_id=None):
        ctx = dict(self.env.context)
        if ctx.get('type') in ('out_invoice', 'out_refund'):
            type_tax_use = {'type_tax_use': 'sale'}
        else:
            type_tax_use = {'type_tax_use': 'purchase'}
        self = self.with_context(type_tax_use)
        result = {'value': {}}

        parent_fiscal_position = ctx.get('parent_fiscal_position')
        parent_fiscal_category_id = ctx.get('parent_fiscal_category_id')

        fiscal_position = fposition_id or parent_fiscal_position or None

        if not parent_fiscal_category_id or not product or not fiscal_position:
            return result
        partner = self.env['res.partner'].browse(partner_id)
        obj_fp_rule = self.env['account.fiscal.position.rule']
        product_fiscal_category_id = obj_fp_rule.with_context(
            ctx).product_fiscal_category_map(
                product, parent_fiscal_category_id, partner.state_id.id)

        if product_fiscal_category_id:
            parent_fiscal_category_id = product_fiscal_category_id
        result['value']['fiscal_category_id'] = parent_fiscal_category_id

        result = self._fiscal_position_map(
            result, partner_id=partner_id, partner_invoice_id=partner_id,
            company_id=company_id, product_id=product,
            fiscal_category_id=parent_fiscal_category_id,
            account_id=result['value'].get('account_id'))

        result_super = super(AccountInvoiceLine, self).product_id_change(
            product, uom_id, qty, name, type, partner_id,
            fposition_id, price_unit, currency_id, company_id)

        result_super['value'].update(result['value'])
        return result_super

    @api.multi
    def onchange_fiscal_category_id(self, partner_id, company_id, product_id,
                                    fiscal_category_id, account_id):
        result = {'value': {}}
        return self._fiscal_position_map(
            result, partner_id=partner_id, partner_invoice_id=partner_id,
            company_id=company_id, fiscal_category_id=fiscal_category_id,
            product_id=product_id, account_id=account_id)

    @api.multi
    def onchange_fiscal_position(self, partner_id, company_id, product_id,
                                 fiscal_category_id, account_id, quantity,
                                 price_unit):
        result = {'value': {}}
        return self._fiscal_position_map(
            result, partner_id=partner_id, partner_invoice_id=partner_id,
            company_id=company_id, fiscal_category_id=fiscal_category_id,
            product_id=product_id, account_id=account_id)