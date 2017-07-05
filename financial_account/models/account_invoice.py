# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import fields, models, api


class AccountInvoice(models.Model):

    _inherit = 'account.invoice'

    def _compute_financial_ids(self):
        document_id = self._name + ',' + str(self.id)
        self.financial_ids = self.env['financial.move'].search(
            [['doc_source_id', '=', document_id]]
        )

    financial_ids = fields.One2many(
        comodel_name='financial.move',
        compute='_compute__financial_ids',
        string=u'Financial Items',
        readonly=True,
        copy=False
    )

    @api.depends('journal_id')
    def _compute_financial_integration(self):
        for record in self:
            if record.journal_id and record.journal_id.financial_integration:
                record.financial_integration = True
            else:
                record.financial_integration = False

    financial_integration = fields.Boolean(
        string=u'Integration with financial',
        compute='_compute_financial_integration',
        store=True,
    )

    def _prepare_move_item(self, item):
        return {
            'document_number': '/',
            'date_maturity': item['date_maturity'],
            'amount': item['debit'] or item['credit'],
            'account_type_id': item['user_type_id'],
        }

    def _prepare_financial_move(self, lines):

        return {
            'date': self.date_invoice,
            'financial_type': '2receive',
            'partner_id': self.partner_id.id,
            'doc_source_id': self._name + ',' + str(self.id),
            'bank_id': 1,
            'company_id': self.company_id and self.company_id.id,
            'currency_id': self.currency_id.id,
            'payment_term_id':
                self.payment_term_id and self.payment_term_id.id or False,
            # 'analytic_account_id':
            # 'payment_mode_id:
            'lines': [self._prepare_move_item(item) for item in lines],
        }

    @api.multi
    def action_financial_create(self, move_lines):
        to_financial = []
        for x, y, item in move_lines:
            account_id = self.env[
                'account.account'].browse(item.get('account_id', []))
            if account_id.internal_type in ('payable', 'receivable'):
                item['user_type_id'] = account_id.user_type_id.id
                to_financial.append(item)

        p = self._prepare_financial_move(to_financial)
        self.env['financial.move']._create_from_dict(p)

    @api.multi
    def finalize_invoice_move_lines(self, move_lines):
        move_lines = super(AccountInvoice, self).finalize_invoice_move_lines(
            move_lines)

        financial_create = self.filtered(
            lambda invoice: invoice.financial_integration)
        financial_create.action_financial_create(move_lines)

        return move_lines

    @api.multi
    def invoice_validate(self):
        super(AccountInvoice, self).invoice_validate()
        for invoice in self:
            invoice.financial_ids.write({
                'document_number': invoice.name or
                invoice.move_id.name or '/'})
            invoice.financial_ids.action_confirm()
