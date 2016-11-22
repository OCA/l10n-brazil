# -*- coding: utf-8 -*-
# Copyright (C) 2009 - TODAY Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import models, fields, api, _
from openerp.addons import decimal_precision as dp

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
    _order = 'date_invoice DESC, internal_number DESC'

    def _compute_receivables(self):
        lines = self.env['account.move.line']
        for line in self.move_id.line_ids:
            if line.account_id.id == self.account_id.id and \
                            line.account_id.user_type_id.type in ('receivable', 'payable') and \
                    self.journal_id.revenue_expense:
                lines |= line
        self.move_line_receivable_id = (lines).sorted()

    state = fields.Selection(
        selection_add=[
            ('sefaz_export', 'Enviar para Receita'),
            ('sefaz_exception', u'Erro de autorização da Receita'),
            ('sefaz_cancelled', 'Cancelado no Sefaz'),
            ('sefaz_denied', 'Denegada no Sefaz'),
        ])
    move_line_receivable_id = fields.Many2many(
        'account.move.line', string='Receivables',
        compute='_compute_receivables')
    document_serie_id = fields.Many2one(
        'l10n_br_account.document.serie', string=u'Série',
        domain="[('fiscal_document_id', '=', fiscal_document_id),\
        ('company_id','=',company_id)]", readonly=True,
        states={'draft': [('readonly', False)]})
    fiscal_document_id = fields.Many2one(
        'l10n_br_account.fiscal.document', string='Documento', readonly=True,
        states={'draft': [('readonly', False)]})
    fiscal_document_electronic = fields.Boolean(
        related='fiscal_document_id.electronic', type='boolean', readonly=True,
        store=True, string='Electronic')
    fiscal_document_code = fields.Char(
        related='fiscal_document_id.code',
        readonly=True,
        store=True,
        string='Document Code')
    fiscal_category_id = fields.Many2one(
        'l10n_br_account.fiscal.category', 'Categoria Fiscal',
        readonly=True, states={'draft': [('readonly', False)]})
    fiscal_position_id = fields.Many2one(
        'account.fiscal.position', 'Fiscal Position', readonly=True,
        states={'draft': [('readonly', False)]}, 
	oldname='fiscal_position',
    )
    account_document_event_ids = fields.One2many(
        'l10n_br_account.document_event', 'document_event_ids',
        u'Eventos')
    fiscal_comment = fields.Text(u'Observação Fiscal')
    cnpj_cpf = fields.Char(
        string=u'CNPJ/CPF',
        related='partner_id.cnpj_cpf',
    )
    legal_name = fields.Char(
        string=u'Razão Social',
        related='partner_id.legal_name',
    )
    ie = fields.Char(
        string=u'Inscrição Estadual',
        related='partner_id.inscr_est',
    )
    revenue_expense = fields.Boolean(
        related='journal_id.revenue_expense',
        readonly=True,
        store=True,
        string='Gera Financeiro'
    )

    @api.one
    @api.constrains('number')
    def _check_invoice_number(self):
        domain = []
        if self.number:
            fiscal_document = self.fiscal_document_id and \
                              self.fiscal_document_id.id or False
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
                raise UserError(u'Não é possível registrar documentos\
                              fiscais com números repetidos.')
    @api.multi
    def name_get(self):
        lista = []
        for obj in self:
            name = obj.internal_number if obj.internal_number else ''
            lista.append((obj.id, name))
        return lista

    _sql_constraints = [
        ('number_uniq', 'unique(number, company_id, journal_id,\
         type, partner_id)', 'Invoice Number must be unique per Company!'),
    ]

    @api.multi
    def finalize_invoice_move_lines(self, move_lines):
        """ finalize_invoice_move_lines(move_lines) -> move_lines

            Hook method to be overridden in additional modules to verify and
            possibly alter the move lines to be created by an invoice, for
            special cases.
            :param move_lines: list of dictionaries with the account.move.lines
            (as for create())
            :return: the (possibly updated) final move_lines to create for this
            invoice
        """
        move_lines = super(
            AccountInvoice, self).finalize_invoice_move_lines(move_lines)
        count = 1
        total = len([x for x in move_lines
                     if x[2]['account_id'] == self.account_id.id])
        number = self.name or self.number
        result = []
        for move_line in move_lines:
            if move_line[2]['debit'] or move_line[2]['credit']:
                if move_line[2]['account_id'] == self.account_id.id:
                    move_line[2]['name'] = '%s/%s-%s' % \
                        (number, count, total)
                    count += 1
                result.append(move_line)
        return result

    def _fiscal_position_id_map(self, result, **kwargs):
        ctx = dict(self._context)
        ctx.update({'use_domain': ('use_invoice', '=', True)})
        if ctx.get('fiscal_category_id'):
            kwargs['fiscal_category_id'] = ctx.get('fiscal_category_id')

        if not kwargs.get('fiscal_category_id'):
            return result

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
    def open_fiscal_document(self):
        ctx = self.env.context.copy()
        ctx.update({
            'fiscal_document_code': self.fiscal_document_code,
            'type': self.type
        })
        return {
            'name': _('Documento Fiscal'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.invoice',
            'context': ctx,
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'res_id': self.id
        }


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    @api.one
    @api.depends('price_unit', 'discount', 'invoice_line_tax_ids', 'quantity',
                 'product_id', 'invoice_id.partner_id', 'invoice_id.currency_id', 'invoice_id.company_id')
    def _compute_price(self):
        currency = self.invoice_id and self.invoice_id.currency_id or None
        price = self.price_unit * (1 - (self.discount or 0.0) / 100.0)
        taxes = False
        if self.invoice_line_tax_ids:
            taxes = self.invoice_line_tax_ids.compute_all(price, currency, self.quantity, product=self.product_id,
                                                          partner=self.invoice_id.partner_id)
        self.price_tax_discount = price_subtotal_signed = taxes['total_excluded'] - taxes[
            'total_tax_discount'] if taxes else self.quantity * price
        self.price_subtotal = taxes['total_excluded'] if taxes else self.quantity * price
        if self.invoice_id.currency_id and self.invoice_id.currency_id != self.invoice_id.company_id.currency_id:
            price_subtotal_signed = self.invoice_id.currency_id.compute(price_subtotal_signed,
                                                                        self.invoice_id.company_id.currency_id)
        sign = self.invoice_id.type in ['in_refund', 'out_refund'] and -1 or 1
        self.price_subtotal_signed = price_subtotal_signed * sign

    invoice_line_tax_id = fields.Many2many(
        'account.tax', 'account_invoice_line_tax', 'invoice_line_id',
        'tax_id', string='Taxes', )  # TODO MIG domain=[('parent_id', '=', False)])
    fiscal_category_id = fields.Many2one(
        'l10n_br_account.fiscal.category', 'Categoria Fiscal')
    fiscal_position_id = fields.Many2one(
        'account.fiscal.position', u'Posição Fiscal',
        domain="[('fiscal_category_id', '=', fiscal_category_id)]")
    price_total = fields.Float(
        string='Amount', store=True, digits=dp.get_precision('Account'),
        readonly=True, compute='_compute_price')

    @api.model
    def move_line_get_item(self, line):
        """
            Overrrite core to fix invoice total account.move
        :param line:
        :return:
        """
        res = super(AccountInvoiceLine, self).move_line_get_item(line)
        res['price'] = line.price_tax_discount
        return res
