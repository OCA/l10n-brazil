# Copyright (C) 2009 - TODAY Renato Lima - Akretion
# Copyright (C) 2019 - TODAY Raphaël Valyi - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields, api


class FiscalInvoice(models.Model):
    _inherit = 'l10n_br_fiscal.document'

    # the following fields collide with account.invoice fields so we use
    # related field alias to be able to write them through account.invoice
    fiscal_doc_partner_id = fields.Many2one(
        related='partner_id', readonly=False)
    fiscal_doc_date = fields.Date(
        related='date', readonly=False)
    fiscal_doc_company_id = fields.Many2one(
        related='company_id', readonly=False)
    fiscal_doc_currency_id = fields.Many2one(
        related='currency_id', readonly=False)
    fiscal_doc_state = fields.Selection(
        related='state', readonly=False)



class AccountInvoice(models.Model):
    _inherit = 'account.invoice'
    _order = 'date_invoice DESC, number DESC'

    _inherits = {'l10n_br_fiscal.document': 'fiscal_document_id'}

    # initial account.invoice inherits on fiscal.document that are
    # disable with active=False in their fiscal_document table.
    # To make these invoices still visible, we set active=True
    # in the invoice table.
    active = fields.Boolean(
        string='Active',
        default=True)

    # this default should be overwritten to False in a module pretending to
    # create fiscal documents from the invoices. But this default here
    # allows to install the l10n_br_account module without creating issues
    # with the existing Odoo invoice (demo or not).
    fiscal_document_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.document',
        string='Fiscal Document',
        required=True,
        ondelete='restrict', # or cascade?
        default=lambda self: self.env.ref(
            'l10n_br_account.fiscal_document_dummy'))


if False: # TODO
    @api.multi
    @api.depends('invoice_line_ids.price_subtotal',
                 'tax_line_ids.amount', 'currency_id',
                 'company_id', 'date_invoice')
    def _compute_amount(self):
        for record in self:
            record.amount_untaxed = sum(
                l.price_subtotal for l in record.invoice_line_ids)
            record.amount_tax = sum(
                t.amount for t in record.tax_line_ids if not
                t.tax_id.tax_discount)
            record.amount_total = record.amount_untaxed + record.amount_tax
            amount_total_company_signed = record.amount_total
            amount_untaxed_signed = record.amount_untaxed
            if (record.currency_id and record.company_id and
                    record.currency_id != record.company_id.currency_id):
                currency_id = record.currency_id.with_context(
                    date=record.date_invoice)
                amount_total_company_signed = currency_id.compute(
                    record.amount_total, record.company_id.currency_id)
                amount_untaxed_signed = currency_id.compute(
                    record.amount_untaxed, record.company_id.currency_id)
            sign = record.type in ['in_refund', 'out_refund'] and -1 or 1
            record.amount_total_company_signed = (
                amount_total_company_signed * sign
            )
            record.amount_total_signed = record.amount_total * sign
            record.amount_untaxed_signed = amount_untaxed_signed * sign

    # Não migrar este módulo para api multi antes da mesma ser removida do core
    @api.one
    @api.depends('move_id.line_ids.amount_residual')
    def _compute_payments(self):

        payment_lines = []
        for line in self.move_id.line_ids.filtered(
                lambda l: l.account_id.id == self.account_id.id and
                self.journal_id.revenue_expense and
                l.account_id.user_type_id.type in ('receivable', 'payable')):
            payment_lines.extend(filter(None, [
                rp.credit_move_id.id for rp in line.matched_credit_ids]))
            payment_lines.extend(filter(None, [
                rp.debit_move_id.id for rp in line.matched_debit_ids]))
        self.payment_move_line_ids = self.env[
            'account.move.line'].browse(list(set(payment_lines)))

    @api.multi
    @api.depends('move_id.line_ids')
    def _compute_receivables(self):
        for record in self:
            lines = self.env['account.move.line']
            for line in record.move_id.line_ids:
                if (line.account_id.id == record.account_id.id and
                        line.account_id.internal_type in
                        ('receivable', 'payable') and
                        record.journal_id.revenue_expense):
                    lines |= line
            record.move_line_receivable_id = lines.sorted()

    state = fields.Selection(
        selection_add=[
            ('sefaz_export', 'Enviar para Receita'),
            ('sefaz_exception', u'Erro de autorização da Receita'),
            ('sefaz_cancelled', 'Cancelado no Sefaz'),
            ('sefaz_denied', 'Denegada no Sefaz')])

    @api.multi
    def name_get(self):
        return [(r.id,
                u"{0}".format(r.number or ''))
                for r in self]

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
