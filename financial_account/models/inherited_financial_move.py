# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from __future__ import division, print_function, unicode_literals

from openerp import api, fields, models, exceptions, _
from openerp.addons.financial.constants import (
    FINANCIAL_DEBT_2PAY,
    FINANCIAL_DEBT_2RECEIVE,
    FINANCIAL_MONEY_IN,
    FINANCIAL_MONEY_OUT,
    FINANCIAL_PAYMENT,
    FINANCIAL_RECEIPT,
)

TYPE2JOURNAL = {
    'receipt_item': ('cash', 'bank'),
    'payment_item': ('cash', 'bank'),
}

DEBT_2RECEIVE_2PAY = (FINANCIAL_DEBT_2RECEIVE, FINANCIAL_DEBT_2PAY)


class FinancialMove(models.Model):
    _inherit = b'financial.move'

    @api.multi
    @api.depends('account_id', 'document_type_id', 'bank_id')
    def _compute_account_move_template_id(self):
        for record in self:
            if record.account_id and record.document_type_id:

                matrix_id = record.account_matrix_id.map_account_matrix_id(
                    account_id=self.account_id.id,
                    document_type_id=record.document_type_id.id
                )
                if matrix_id and record.type:
                    if record.type in DEBT_2RECEIVE_2PAY:

                        record.journal_id = \
                            matrix_id.journal_id
                    else:
                        record.journal_id = record.bank_id.journal_id

                    account_move_template_id = \
                        record.account_matrix_id.map_account_move_template_id(
                            account_id=record.account_id.id,
                            document_type_id=record.document_type_id.id,
                            matrix_id=matrix_id.id,
                            type=record.type
                        )
                    record.account_move_template_id = (
                        account_move_template_id and
                        account_move_template_id.id or
                        False
                    )

    journal_id = fields.Many2one(
        compute='_compute_account_move_template_id',
        comodel_name='account.journal',
        string='Journal',
        ondelete='restrict',
        store=True,
    )
    account_move_template_id = fields.Many2one(
        compute='_compute_account_move_template_id',
        comodel_name='financial.account.move.template',
        string='Account move template',
        ondelete='restrict',
        store=True,
    )
    account_move_id = fields.Many2one(
        comodel_name='account.move',
        string='Account move',
        ondelete='restrict',
        copy=False,
        readonly=True,
    )
    #
    # The correct name of this field is ... line_ids
    # But only in v10, than we have to migrate it.
    #
    account_move_line_id = fields.One2many(
        comodel_name='account.move.line',
        inverse_name='move_id',
        string='Partidas do lançamento contábil',
        related='account_move_id.line_id',
        readonly=True,
    )
    require_accountant_review = fields.Boolean(
        string='Require accountant review'
    )
    account_matrix_id = fields.Many2one(
        comodel_name='financial.account.move.matrix',
        string='Accounting Matrix',
        ondelete='restrict',
    )

    @api.onchange('account_id')
    def onchange_account_id(self):

        if self.account_id:
            document_type_length = len(self.account_id.account_matrix_ids)
            document_type_id = \
                self.account_id.account_matrix_ids.mapped('document_type_id')

            if self.type in DEBT_2RECEIVE_2PAY:
                self.journal_id = self.account_id.journal_id

            if (document_type_id and
                    len(document_type_id) == document_type_length):
                return {'domain': {
                    'document_type_id': [('id', 'in', document_type_id.ids)]
                }}
            else:
                return {'domain': {'document_type_id': False}}

    @api.multi
    def create_account_move(self):
        account_move = self.env['account.move']

        for move in self:
            if move.account_move_line_id:
                continue

            line_id = []

            error = ''

            if not move.account_move_template_id:
                error += _("- Move template not found\n")
            if not move.journal_id:
                if move.type in DEBT_2RECEIVE_2PAY:
                    error += _("- Financial account without journal\n")
                else:
                    error += _("- Bank account without journal\n")
            if error:
                raise exceptions.ValidationError(
                    _('Account configuration error: \n' + error)
                )

            fields_already_accounted = []

            move.create_account_move_line(
                account_move,
                move.account_move_template_id,
                line_id,
                fields_already_accounted=fields_already_accounted
            )

            vals = {
                'financial_move_id': move.id,
                'ref': move.document_number,
                'partner_id': move.partner_id.id,
                'company_id': move.company_id.id,
                'date': move.date_document,
                'line_id': line_id,
                'journal_id': move.journal_id.id,
            }

            self.account_move_id = account_move.create(vals)

            if len(move.payment_ids) > 0:
                move.payment_ids.create_account_move()

    @api.multi
    def create_account_move_line(self, account_move, move_template, line_id,
                                 fields_already_accounted=False):
        self.ensure_one()

        diff_currency = self.currency_id != self.company_id.currency_id

        if not fields_already_accounted:
            fields_already_accounted = []

        for template_item in move_template.item_ids:
            if not getattr(self, template_item.field, False):
                continue

            if template_item.field in fields_already_accounted:
                continue

            value = getattr(self, template_item.field, 0)

            if not value:
                continue

            vals = {
                'move_id': account_move.id,
                'financial_move_id': self.id,
                'name': self.document_number,
                'narration': template_item.field,
                'debit': value,
                'currency_id': diff_currency and self.currency_id.id,
            }

            #
            # For receipts and payments, we use the configurations from
            # the document type of their respectiv debts
            #
            if self.type in DEBT_2RECEIVE_2PAY:
                partner = self.partner_id
            else:
                partner = self.debt_id.partner_id

            #
            # Default debit and credit accounts, per financial move type
            #
            account_debit = None
            if template_item.account_debit_id:
                account_debit = template_item.account_debit_id
            else:
                if self.type == FINANCIAL_DEBT_2RECEIVE:
                    if partner.property_account_receivable_id:
                        account_debit = \
                            partner.property_account_receivable_id

                elif self.type == FINANCIAL_DEBT_2PAY:
                    if account_move.journal_id.default_debit_account_id:
                        account_debit = \
                            account_move.journal_id.default_debit_account_id

                elif self.type == FINANCIAL_RECEIPT:
                    if self.bank_id.account_id:
                        account_debit = self.bank_id.account_id

                elif self.type == FINANCIAL_PAYMENT:
                    if partner.property_account_payable_id:
                        account_debit = \
                            partner.property_account_payable_id

                elif self.type == FINANCIAL_MONEY_IN:
                    if self.bank_id.account_id:
                        account_debit = self.bank_id.account_id

                elif self.type == FINANCIAL_MONEY_OUT:
                    if account_move.journal_id.default_debit_account_id:
                        account_debit = \
                            account_move.journal_id.default_debit_account_id

            if account_debit is None:
                # raise
                pass
            else:
                vals['account_id'] = account_debit.id

            line_id.append((0, 0, vals))

            vals = {
                'move_id': account_move.id,
                'financial_move_id': self.id,
                'name': self.document_number,
                'narration': template_item.field,
                'credit': value,
                'currency_id': diff_currency and self.currency_id.id,
            }

            account_credit = None
            if template_item.account_credit_id:
                account_credit = template_item.account_credit_id
            else:
                if self.type == FINANCIAL_DEBT_2RECEIVE:
                    if account_move.journal_id.default_credit_account_id:
                        account_debit = \
                            account_move.journal_id.default_credit_account_id

                elif self.type == FINANCIAL_DEBT_2PAY:
                    if partner.property_account_payable_id:
                        account_credit = \
                            partner.property_account_payable_id

                elif self.type == FINANCIAL_RECEIPT:
                    if partner.property_account_receivable_id:
                        account_credit = \
                            partner.property_account_receivable_id

                elif self.type == FINANCIAL_PAYMENT:
                    if self.bank_id.account_id:
                        account_credit = self.bank_id.account_id

                elif self.type == FINANCIAL_MONEY_IN:
                    if account_move.journal_id.default_credit_account_id:
                        account_debit = \
                            account_move.journal_id.default_credit_account_id

                elif self.type == FINANCIAL_MONEY_OUT:
                    if self.bank_id.account_id:
                        account_credit = self.bank_id.account_id

            if account_debit is None:
                # raise
                pass
            else:
                vals['account_id'] = account_credit.id

            line_id.append((0, 0, vals))

            fields_already_accounted.append(template_item.field)

        if move_template.parent_id:
            self.create_account_move_line(
                account_move,
                move_template.parent_id, line_id,
                fields_already_accounted=fields_already_accounted
            )

    @api.multi
    def action_confirm(self):
        super(FinancialMove, self).action_confirm()
        for record in self:
            if record.account_move_line_id:
                continue
            record._compute_account_move_template_id()
            record.create_account_move()

    @api.multi
    def do_after_create(self, result, values):
        result = super(FinancialMove, self).do_after_create(result, values)

        #
        # Create automatically account moves for payment_item and receipt_item
        #
        to_create_move = result.filtered(
            lambda r:
            r.type not in DEBT_2RECEIVE_2PAY and not r.account_move_id)
        to_create_move.create_account_move()

        return result

    @api.multi
    def action_cancel(self, reason):
        super(FinancialMove, self).action_cancel(reason)
        moves = self.env['account.move']
        for record in self:
            if record.account_move_id:
                moves += record.account_move_id
            if record.payment_ids:
                for payment_line in record.payment_ids:
                    if payment_line.account_move_id:
                        raise exceptions.ValiationError(
                            _('You cannot cancel a financial which is paid.'
                              ' You need to cancel the related payment '
                              'entries first.'))
        # Detach the move ids:
        self.write({'account_move_id': False})
        if moves:
            # second, invalidate the move(s)
            moves.button_cancel()
            # delete the move this financial was pointing to
            # Note that the corresponding move_lines and move_reconciles
            # will be automatically deleted too
            moves.unlink()
        return True
