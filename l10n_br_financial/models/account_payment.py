# Copyright 2020 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _

from .contants import (
    FINANCIAL_DEBT,
    FINANCIAL_IN_OUT
)


class AccountPayment(models.Model):

    _inherit = 'account.payment'

    @api.depends('date_maturity')
    def _compute_date_business_maturity(self):
        # for move in self:
        #     if move.date_maturity:
        #         move.date_business_maturity = move.date_maturity
        for record in self:
            if record.date_maturity:
                record.date_business_maturity = record.date_maturity
                # record.date_business_maturity = self.env[
                #     'resource.calendar'].proximo_dia_util_bancario(
                #     fields.Date.from_string(record.date_maturity))

    @api.depends('debt_id')
    def _compute_debt_ids(self):
        for payment in self:
            if payment.debt_id:
                payment.debt_ids = [payment.debt_id.id]
            else:
                payment.debt_ids = False

    payment_type = fields.Selection(
        selection_add=FINANCIAL_DEBT,
    )
    date_maturity = fields.Date(
        string='Maturity date',
        index=True,
    )
    date_business_maturity = fields.Date(
        string='Business maturity date',
        store=True,
        compute='_compute_date_business_maturity',
        index=True,
    )
    date_payment = fields.Date(
        string='Payment date',
        copy=False,
    )
    date_credit_debit = fields.Date(
        string='Credit/debit date',
    )
    date_cancel = fields.Date(
        string='Cancel date',
    )
    date_refund = fields.Date(
        string='Refund date',
    )
    debit = fields.Monetary()
    credit = fields.Monetary()
    date = fields.Date()
    account_id = fields.Many2one(
        comodel_name='account.account',
    )

    #
    # Relations
    #

    #
    # Relations to other debts and payments
    #
    debt_id = fields.Many2one(
        comodel_name='account.payment',
        string='Debt',
        # domain=[('payment_type', 'in', FINANCIAL_IN_OUT)],
        index=True,
    )
    payment_ids = fields.One2many(
        comodel_name='account.payment',
        inverse_name='debt_id',
    )
    debt_ids = fields.One2many(
        comodel_name='account.payment',
        compute='_compute_debt_ids',
    )

    document_id = fields.Many2one(
        comodel_name='l10n_br_document.fiscal'
    )

    def generate_move(self, move_lines):
        for record in self:
            if record.amount:
                data = {
                    'name': '/',
                    'debit': record.amount,
                    'currency_id':
                        record.currency_id and record.currency_id.id or False,
                    'partner_id': record.partner_id and record.partner_id.id or False,
                    'account_id': record.partner_id.property_account_receivable_id.id,
                    'date_maturity': record.date_maturity,
                    'financial_payment_id': record.id,
                }
                move_lines.append((0, 0, data))
