# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from __future__ import division, print_function, unicode_literals

from openerp import api, fields, models
from openerp.addons.financial.constants import (
    FINANCIAL_DEBT_2PAY,
    FINANCIAL_DEBT_2RECEIVE,
    FINANCIAL_MONEY_IN,
    FINANCIAL_MONEY_OUT,
    FINANCIAL_PAYMENT,
    FINANCIAL_RECEIPT,
)


class FinancialMove(models.Model):
    _inherit = b'financial.move'

    #
    # Accounting
    #
    account_journal_id = fields.Many2one(
        comodel_name='account.journal',
        string='Journal',
        ondelete='restrict',
    )
    account_move_template_id = fields.Many2one(
        comodel_name='financial.account.move.template',
        string='Account move template',
        ondelete='restrict',
    )
    account_move_id = fields.Many2one(
        comodel_name='account.move',
        string='Account move',
        ondelete='restrict',
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
    )

    def create_account_move(self):
        for move in self:
            vals = {
                'financial_move_id': move.id,
                'ref': move.document_number,
                'partner_id': move.partner_id.id,
                'company_id': move.company_id.id,
                'date': move.date_document,
            }

            #
            # For receipts and payments, we use the configurations from
            # the document type of their respectiv debts
            #
            if move.type in (FINANCIAL_RECEIPT, FINANCIAL_PAYMENT):
                financial_account = move.debt_id.account_id
            else:
                financial_account = move.account_id

            if move.account_journal_id:
                vals['journal_id'] = move.account_journal_id.id
            elif financial_account.account_journal_id:
                vals['journal_id'] = financial_account.account_journal_id.id

            if move.account_move_id:
                if move.account_move_id.state != 'draft':
                    # raise
                    continue
                account_move = move.account_move_id
                account_move.write(vals)
            else:
                account_move = self.env['account.move'].create(vals)
                move.account_move_id = account_move

            line_id = [(5, 0, {})]

            move_template = None
            if move.account_move_template_id:
                move_template = move.account_move_template_id
            else:
                if move.type == FINANCIAL_DEBT_2RECEIVE and \
                        financial_account.account_move_template_2receive_id:
                    move_template = \
                        financial_account.account_move_template_2receive_id

                elif move.type == FINANCIAL_DEBT_2PAY and \
                        financial_account.account_move_template_2pay_id:
                    move_template = \
                        financial_account.account_move_template_2pay_id

                elif move.type == FINANCIAL_RECEIPT and \
                        financial_account.\
                        account_move_template_receipt_item_id:
                    move_template = \
                        financial_account.account_move_template_receipt_item_id

                elif move.type == FINANCIAL_PAYMENT and \
                        financial_account.\
                        account_move_template_payment_item_id:
                    move_template = \
                        financial_account.account_move_template_payment_item_id
                elif move.type == FINANCIAL_MONEY_IN and \
                        financial_account.account_move_template_money_in_id:
                    move_template = \
                        financial_account.account_move_template_money_in_id
                elif move.type == FINANCIAL_MONEY_OUT and \
                        financial_account.account_move_template_money_out_id:
                    move_template = \
                        financial_account.account_move_template_money_out_id

            if move_template is None:
                # raise
                pass

            fields_already_accounted = []
            move.create_account_move_line(
                account_move,
                move_template,
                line_id,
                fields_already_accounted=fields_already_accounted
            )

            account_move.write({'line_id': line_id})

            if len(move.payment_ids) > 0:
                move.payment_ids.create_account_move()

    def create_account_move_line(self, account_move, move_template, line_id,
                                 fields_already_accounted=[]):
        self.ensure_one()
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
                'currency_id': self.currency_id.id,
            }

            #
            # For receipts and payments, we use the configurations from
            # the document type of their respectiv debts
            #
            if self.type in (FINANCIAL_RECEIPT, FINANCIAL_PAYMENT):
                partner = self.debt_id.partner_id
            else:
                partner = self.partner_id

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

            line_id.append([0, 0, vals])

            vals = {
                'move_id': account_move.id,
                'financial_move_id': self.id,
                'name': self.document_number,
                'narration': template_item.field,
                'credit': value,
                'currency_id': self.currency_id.id,
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

            line_id.append([0, 0, vals])

            fields_already_accounted.append(template_item.field)

        if move_template.parent_id:
            self.create_account_move_line(
                account_move,
                move_template.parent_id, line_id,
                fields_already_accounted=fields_already_accounted
            )

    @api.model
    def create(self, vals):
        financial_move_ids = super(FinancialMove, self).create(vals)
        financial_move_ids.create_account_move()
        return financial_move_ids

    @api.multi
    def _write(self, vals):
        res = super(FinancialMove, self)._write(vals)
        self.create_account_move()
        return res

    @api.multi
    def do_after_unlink(self):
        for record in self:
            record.account_move_id.unlink()
