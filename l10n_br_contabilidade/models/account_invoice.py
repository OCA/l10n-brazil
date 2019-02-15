# -*- coding: utf-8 -*-
# Copyright 2018 ABGF
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    number = fields.Char(
        string='number',
        compute='_compute_number',
        related=False,
    )

    move_id = fields.One2many(
        string=u'Lançamentos Contábeis',
        comodel_name='account.move',
        inverse_name='account_invoice_id',
        copy=False,
    )

    @api.depends('internal_number')
    def _compute_number(self):
        for record in self:
            record.number = record.internal_number

    @api.multi
    def _compute_residual(self):
        self.residual = 0.0
        # Each partial reconciliation is considered only once for each invoice it appears into,
        # and its residual amount is divided by this number of invoices
        partial_reconciliations_done = []
        for move in self.move_id:
            for line in move.line_id:
                if line.account_id.type not in ('receivable', 'payable'):
                    continue
                if line.reconcile_partial_id and line.reconcile_partial_id.id in partial_reconciliations_done:
                    continue
                # Get the correct line residual amount
                if line.currency_id == self.currency_id:
                    line_amount = line.amount_residual_currency if line.currency_id else line.amount_residual
                else:
                    from_currency = line.company_id.currency_id.with_context(
                        date=line.date)
                    line_amount = from_currency.compute(line.amount_residual,
                                                        self.currency_id)
                # For partially reconciled lines, split the residual amount
                if line.reconcile_partial_id:
                    partial_reconciliation_invoices = set()
                    for pline in line.reconcile_partial_id.line_partial_ids:
                        if pline.invoice and self.type == pline.invoice.type:
                            partial_reconciliation_invoices.update(
                                [pline.invoice.id])
                    line_amount = self.currency_id.round(
                        line_amount / len(partial_reconciliation_invoices))
                    partial_reconciliations_done.append(
                        line.reconcile_partial_id.id)
                self.residual += line_amount
        self.residual = max(self.residual, 0.0)

    @api.depends(
        'move_id.line_id.reconcile_id.line_id',
        'move_id.line_id.reconcile_partial_id.line_partial_ids',
    )
    def _compute_receivables(self):
        lines = self.env['account.move.line']
        for move in self.move_id:
            for line in move.line_id:
                if line.account_id.id == self.account_id.id and \
                        line.account_id.type in ('receivable', 'payable') and \
                        self.journal_id.revenue_expense:
                    lines |= line
        self.move_line_receivable_id = (lines).sorted()

    @api.depends(
        'move_id.line_id.reconcile_id.line_id',
        'move_id.line_id.reconcile_partial_id.line_partial_ids',
    )
    def _compute_payments(self):
        partial_lines = lines = self.env['account.move.line']
        for move in self.move_id:
            for line in move.line_id:
                if line.account_id != self.account_id:
                    continue
                if line.reconcile_id:
                    lines |= line.reconcile_id.line_id
                elif line.reconcile_partial_id:
                    lines |= line.reconcile_partial_id.line_partial_ids
                partial_lines += line
        self.payment_ids = (lines - partial_lines).sorted()

    @api.depends(
        'move_id.line_id.account_id',
        'move_id.line_id.reconcile_id.line_id',
        'move_id.line_id.reconcile_partial_id.line_partial_ids',
    )
    def _compute_move_lines(self):
        # Give Journal Items related to the payment reconciled to this invoice.
        # Return partial and total payments related to the selected invoice.
        self.move_lines = self.env['account.move.line']
        if not self.move_id:
            return
        data_lines = []
        for move in self.move_id:
            data_lines += move.line_id.filtered(
                lambda l: l.account_id == self.account_id)
        partial_lines = self.env['account.move.line']
        for data_line in data_lines:
            if data_line.reconcile_id:
                lines = data_line.reconcile_id.line_id
            elif data_line.reconcile_partial_id:
                lines = data_line.reconcile_partial_id.line_partial_ids
            else:
                lines = self.env['account.move.line']
            partial_lines += data_line
            self.move_lines = lines - partial_lines
