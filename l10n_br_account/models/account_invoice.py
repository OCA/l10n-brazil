# -*- coding: utf-8 -*-
# Copyright (C) 2009 - TODAY Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields, api, _
from odoo.exceptions import Warning as UserError

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
    _order = 'date_invoice DESC, number DESC'

    @api.multi
    @api.depends('invoice_line_ids.price_subtotal',
                 'tax_line_ids.amount', 'currency_id',
                 'company_id', 'date_invoice')
    def _compute_amount(self):
        for record in self:
            record.amount_untaxed = sum(l.price_subtotal
                                      for l in record.invoice_line_ids)
            record.amount_tax = sum(t.amount for t in record.tax_line_ids
                                  if not t.tax_id.tax_discount)
            record.amount_total = record.amount_untaxed + record.amount_tax
            amount_total_company_signed = record.amount_total
            amount_untaxed_signed = record.amount_untaxed
            if (record.currency_id and record.company_id and
                    record.currency_id != record.company_id.currency_id):
                currency_id = record.currency_id.with_context(date=record.date_invoice)
                amount_total_company_signed = currency_id.compute(
                    record.amount_total, record.company_id.currency_id)
                amount_untaxed_signed = currency_id.compute(
                    record.amount_untaxed, record.company_id.currency_id)
            sign = record.type in ['in_refund', 'out_refund'] and -1 or 1
            record.amount_total_company_signed = amount_total_company_signed * sign
            record.amount_total_signed = record.amount_total * sign
            record.amount_untaxed_signed = amount_untaxed_signed * sign

    def _compute_receivables(self):
        lines = self.env['account.move.line']
        for line in self.move_id.line_ids:
            if (line.account_id.id == self.account_id.id and
                    self.journal_id.revenue_expense and
                    line.account_id.user_type_id.type in ('receivable',
                                                          'payable')):
                lines |= line
        self.move_line_receivable_id = (lines).sorted()

    state = fields.Selection(
        selection_add=[
            ('sefaz_export', 'Enviar para Receita'),
            ('sefaz_exception', u'Erro de autorização da Receita'),
            ('sefaz_cancelled', 'Cancelado no Sefaz'),
            ('sefaz_denied', 'Denegada no Sefaz')])

    move_line_receivable_id = fields.Many2many(
        comodel_name='account.move.line',
        string=u'Receivables',
        compute='_compute_receivables')

    document_serie_id = fields.Many2one(
        comodel_name='l10n_br_account.document.serie',
        string=u'Série',
        domain="[('fiscal_document_id', '=', fiscal_document_id),"
               "('company_id', '=', company_id)]",
        readonly=True,
        states={'draft': [('readonly', False)]})

    fiscal_document_id = fields.Many2one(
        comodel_name='l10n_br_account.fiscal.document',
        string=u'Documento',
        readonly=True,
        states={'draft': [('readonly', False)]})

    fiscal_document_electronic = fields.Boolean(
        related='fiscal_document_id.electronic',
        store=True,
        readonly=True,
        string='Electronic')

    fiscal_document_code = fields.Char(
        related='fiscal_document_id.code',
        store=True,
        readonly=True,
        string='Document Code')

    fiscal_category_id = fields.Many2one(
        comodel_name='l10n_br_account.fiscal.category',
        string=u'Categoria Fiscal',
        readonly=True,
        states={'draft': [('readonly', False)]})

    fiscal_position_id = fields.Many2one(
        comodel_name='account.fiscal.position',
        string=u'Fiscal Position',
        readonly=True,
        states={'draft': [('readonly', False)]},
        oldname='fiscal_position')

    account_document_event_ids = fields.One2many(
        comodel_name='l10n_br_account.document_event',
        inverse_name='document_event_ids',
        string=u'Eventos')

    fiscal_comment = fields.Text(
        string=u'Observação Fiscal')

    cnpj_cpf = fields.Char(
        string=u'CNPJ/CPF',
        related='partner_id.cnpj_cpf')

    legal_name = fields.Char(
        string=u'Razão Social',
        related='partner_id.legal_name')

    ie = fields.Char(
        string=u'Inscrição Estadual',
        related='partner_id.inscr_est')

    revenue_expense = fields.Boolean(
        related='journal_id.revenue_expense',
        readonly=True,
        store=True,
        string=u'Gera Financeiro')

    @api.multi
    def name_get(self):
        lista = []
        for obj in self:
            name = obj.number or ''
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
        move_lines = super(AccountInvoice, self).\
            finalize_invoice_move_lines(move_lines)

        count = 1
        total = len([x for x in move_lines
                     if x[2]['account_id'] == self.account_id.id])
        number = self.name or self.number or self.origin or False
        if number:
            result = []
            for move_line in move_lines:
                if move_line[2]['debit'] or move_line[2]['credit']:
                    if move_line[2]['account_id'] == self.account_id.id:
                        move_line[2]['name'] = '%s/%s-%s' % \
                            (number, count, total)
                        count += 1
                    result.append(move_line)
        else:
            result = move_lines
        return result

    @api.model
    def invoice_line_move_line_get(self):
        result = super(AccountInvoice, self).invoice_line_move_line_get()
        i = 0
        for l in self.invoice_line_ids:
            result[i]['price'] = l.price_subtotal - l.amount_tax_discount
            i += 1
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
            raise UserError(
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
