# Copyright 2020 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _

from .contants import (
    SIGN_POSITIVE,
    FINANCIAL_DEBT,
    FINANCIAL_DEBT_2RECEIVE,
    FINANCIAL_DEBT_2PAY,
    FINANCIAL_STATE,
    FINANCIAL_TYPE,
    FINANCIAL_TYPE_CODE,
    FINANCIAL_DEBT_STATUS,
    FINANCIAL_DEBT_STATUS_DUE,
    FINANCIAL_DEBT_STATUS_DUE_TODAY,
    FINANCIAL_DEBT_STATUS_OVERDUE,
    FINANCIAL_DEBT_STATUS_PAID,
    FINANCIAL_DEBT_STATUS_PAID_PARTIALLY,
    FINANCIAL_DEBT_STATUS_CANCELLED,
    FINANCIAL_DEBT_STATUS_CANCELLED_PARTIALLY,
    FINANCIAL_DEBT_STATUS_CONSIDERS_OPEN,
    FINANCIAL_DEBT_STATUS_CONSIDERS_PAID,
    FINANCIAL_DEBT_STATUS_CONSIDERS_CANCELLED,
    FINANCIAL_DEBT_CONCISE_STATUS,
    FINANCIAL_DEBT_CONCISE_STATUS_OPEN,
    FINANCIAL_DEBT_CONCISE_STATUS_PAID,
    FINANCIAL_DEBT_CONCISE_STATUS_CANCELLED,
)


class AccountPayment(models.Model):

    _inherit = 'account.payment'

    @api.depends('payment_type')
    def _compute_sign(self):
        for move in self:
            if move.payment_type in SIGN_POSITIVE:
                move.sign = 1
            else:
                move.sign = -1

    @api.depends('amount',
                 'amount_interest', 'amount_penalty', 'amount_other_credits',
                 'amount_discount', 'amount_other_debits', 'amount_bank_fees',
                 'payment_ids.amount',
                 'payment_ids.amount_interest', 'payment_ids.amount_penalty',
                 'payment_ids.amount_other_credits',
                 'payment_ids.amount_discount',
                 'payment_ids.amount_other_debits',
                 'payment_ids.amount_bank_fees',
                 )
    def _compute_total_and_residual(self):
        for move in self:
            amount_total = move.amount
            amount_total += move.amount_interest
            amount_total += move.amount_penalty
            amount_total += move.amount_other_credits
            amount_total -= move.amount_discount
            amount_total -= move.amount_other_debits
            amount_total -= move.amount_bank_fees

            amount_paid_document = 0
            amount_paid_interest = 0
            amount_paid_penalty = 0
            amount_paid_other_credits = 0
            amount_paid_discount = 0
            amount_paid_other_debits = 0
            amount_paid_bank_fees = 0
            amount_paid_total = 0

            amount_residual = 0
            amount_cancel = 0
            amount_refund = 0

            if move.payment_type in (FINANCIAL_DEBT_2RECEIVE, FINANCIAL_DEBT_2PAY):
                for payment in move.payment_ids:
                    amount_paid_document += payment.amount
                    amount_paid_interest += payment.amount_interest
                    amount_paid_penalty += payment.amount_penalty
                    amount_paid_other_credits += payment.amount_other_credits
                    amount_paid_discount += payment.amount_discount
                    amount_paid_other_debits += payment.amount_other_debits
                    amount_paid_bank_fees += payment.amount_bank_fees
                    amount_paid_total += payment.amount_total

                amount_residual = amount_total - amount_paid_document

                if move.date_cancel:
                    amount_cancel = amount_residual

                if amount_residual < 0:
                    amount_refund = amount_residual * -1
                    amount_residual = 0

            move.amount_total = amount_total
            move.amount_residual = amount_residual
            move.amount_cancel = amount_cancel
            move.amount_refund = amount_refund
            move.amount_paid_document = amount_paid_document
            move.amount_paid_interest = amount_paid_interest
            move.amount_paid_penalty = amount_paid_penalty
            move.amount_paid_other_credits = amount_paid_other_credits
            move.amount_paid_discount = amount_paid_discount
            move.amount_paid_other_debits = amount_paid_other_debits
            move.amount_paid_bank_fees = amount_paid_bank_fees
            move.amount_paid_total = amount_paid_total


    @api.depends('date_business_maturity', 'amount_total', 'amount',
                 'amount_residual', 'amount_paid_document', 'date_cancel')
    def _compute_debt_status(self):
        for move in self:
            if move.payment_type not in (FINANCIAL_DEBT_2RECEIVE, FINANCIAL_DEBT_2PAY):
                continue

            if move.date_cancel:
                if move.amount_paid_document > 0:
                    move.debt_status = \
                        FINANCIAL_DEBT_STATUS_CANCELLED_PARTIALLY
                else:
                    move.debt_status = FINANCIAL_DEBT_STATUS_CANCELLED

            elif move.amount_paid_document > 0:
                if move.amount_residual > 0:
                    move.debt_status = FINANCIAL_DEBT_STATUS_PAID_PARTIALLY
                else:
                    move.debt_status = FINANCIAL_DEBT_STATUS_PAID

            else:
                today = fields.Date.context_today(move)
                due_date = move.date_business_maturity

                if due_date and due_date > today:
                    move.debt_status = FINANCIAL_DEBT_STATUS_DUE

                elif due_date == today:
                    move.debt_status = FINANCIAL_DEBT_STATUS_DUE_TODAY

                else:
                    move.debt_status = FINANCIAL_DEBT_STATUS_OVERDUE

            if move.debt_status in FINANCIAL_DEBT_STATUS_CONSIDERS_OPEN:
                move.debt_concise_status = FINANCIAL_DEBT_CONCISE_STATUS_OPEN
            elif move.debt_status in FINANCIAL_DEBT_STATUS_CONSIDERS_PAID:
                move.debt_concise_status = FINANCIAL_DEBT_CONCISE_STATUS_PAID
            elif move.debt_status in FINANCIAL_DEBT_STATUS_CONSIDERS_CANCELLED:
                move.debt_concise_status = \
                    FINANCIAL_DEBT_CONCISE_STATUS_CANCELLED

            if move.debt_status == FINANCIAL_DEBT_STATUS_PAID:
                move.reconciled = True
            else:
                move.reconciled = False

    @api.depends('debt_id', 'sign', 'date_maturity', 'payment_date')
    def _compute_mis_data(self):
        # FIXME: !!! Use reconcile and others fields
        for record in self:
            if record.sign == 1:
                record.credit = record.amount
            else:
                record.debit = record.amount

            if record.payment_date:
                record.date = record.payment_date
            else:
                record.date = record.date_maturity

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

    # @api.depends('company_id.today_date')
    # def _compute_arrears_days(self):
    #     def date_value(date_str):
    #         return fields.Date.from_string(date_str)
    #
    #     for record in self:
    #         date_diference = False
    #         if record.debt_status == 'paid' and record.date_payment:
    #             date_diference = record.date_payment - record.date_business_maturity
    #         elif record.debt_status == 'overdue':
    #             date_diference = \
    #                 record.company_id.today_date - record.date_business_maturity
    #         arrears = date_diference and date_diference.days or 0
    #         record.arrears_days = arrears

    journal_id = fields.Many2one(
        domain=[(1,'=', 1)],
    )

    payment_type = fields.Selection(
        selection_add=FINANCIAL_DEBT,
    )
    doc_source_id = fields.Reference(
        selection=[],
        string='Source Document',
        readonly=True,
    )
    account_id = fields.Many2one(
        comodel_name='account.account',
    )
    document_type_id = fields.Char(
        # comodel_name='financial.document.type',
        string='Document type',
        # ondelete='restrict',
        index=True,
        # required=True,
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

    #
    # Mis builder Fields
    #

    debit = fields.Monetary(
        compute='_compute_mis_data',
        store=True,
    )
    credit = fields.Monetary(
        compute='_compute_mis_data',
        store = True,
    )
    date = fields.Date(
        compute='_compute_mis_data',
        store=True,
    )


    sign = fields.Integer(
        string='Sign',
        compute='_compute_sign',
        store=True,
    )

    #
    # Move amounts
    #
    amount_interest = fields.Monetary(
        string='Interest',
        digits=(18, 2),
    )
    amount_penalty = fields.Monetary(
        string='Penalty',
        digits=(18, 2),
    )
    amount_other_credits = fields.Monetary(
        string='Other credits',
        digits=(18, 2),
    )
    amount_discount = fields.Monetary(
        string='Discount',
        digits=(18, 2),
    )
    amount_other_debits = fields.Monetary(
        string='Other debits',
        digits=(18, 2),
    )
    amount_bank_fees = fields.Monetary(
        string='Bank fees',
        digits=(18, 2),
    )
    amount_refund = fields.Float(
        string='Refund amount',
        compute='_compute_total_and_residual',
        store=True,
        digits=(18, 2),
    )
    amount_cancel = fields.Float(
        string='Cancelled amount',
        compute='_compute_total_and_residual',
        store=True,
        digits=(18, 2),
    )
    amount_total = fields.Monetary(
        string='Total',
        compute='_compute_total_and_residual',
        store=True,
        digits=(18, 2),
    )

    #
    # Amount fields to sum up all payments linked to a debt
    #
    amount_paid_document = fields.Float(
        string='Paid Document Amount',
        compute='_compute_total_and_residual',
        store=True,
        digits=(18, 2),
    )
    amount_paid_interest = fields.Float(
        string='Paid Interest',
        compute='_compute_total_and_residual',
        store=True,
        digits=(18, 2),
    )
    amount_paid_penalty = fields.Float(
        string='Paid Penalty',
        compute='_compute_total_and_residual',
        store=True,
        digits=(18, 2),
    )
    amount_paid_other_credits = fields.Float(
        string='Paid Other credits',
        compute='_compute_total_and_residual',
        store=True,
        digits=(18, 2),
    )
    amount_paid_discount = fields.Float(
        string='Paid Discount',
        compute='_compute_total_and_residual',
        store=True,
        digits=(18, 2),
    )
    amount_paid_other_debits = fields.Float(
        string='Paid Other debits',
        compute='_compute_total_and_residual',
        store=True,
        digits=(18, 2),
    )
    amount_paid_bank_fees = fields.Float(
        string='Paid Bank fees',
        compute='_compute_total_and_residual',
        store=True,
        digits=(18, 2),
    )
    amount_paid_total = fields.Float(
        string='Paid Total',
        compute='_compute_total_and_residual',
        store=True,
        digits=(18, 2),
    )
    amount_residual = fields.Float(
        string='Residual',
        compute='_compute_total_and_residual',
        store=True,
        digits=(18, 2),
    )

    #
    # Move interest and discount forecast
    #
    interest_rate = fields.Float(
        string='Interest rate',
        digits=(18, 10),
    )
    date_interest = fields.Date(
        string='Interest since',
    )
    amount_interest_forecast = fields.Monetary(
        string='Interest forecast',
        digits=(18, 2),
    )
    penalty_rate = fields.Float(
        string='Penalty rate',
        digits=(18, 10),
    )
    date_penalty = fields.Date(
        string='Penalty since',
    )
    amount_penalty_forecast = fields.Monetary(
        string='Penalty forecast',
        digits=(18, 2),
    )
    discount_rate = fields.Float(
        string='Penalty rate',
        digits=(18, 10),
    )
    date_discount = fields.Date(
        string='Discount up to',
    )
    amount_discount_forecast = fields.Monetary(
        string='Discount forecast',
        digits=(18, 2),
    )
    amount_total_forecast = fields.Monetary(
        string='Total forecast',
        digits=(18, 2),
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

    #
    # Debt status
    #
    debt_status = fields.Selection(
        string='Debt Status',
        selection=FINANCIAL_DEBT_STATUS,
        compute='_compute_debt_status',
        store=True,
        index=True,
    )
    debt_concise_status = fields.Selection(
        string='Debt Concise Status',
        selection=FINANCIAL_DEBT_CONCISE_STATUS,
        compute='_compute_debt_status',
        store=True,
        index=True,
    )
    reconciled = fields.Boolean(
        string='Paid/Reconciled',
        compute='_compute_debt_status',
        store=True,
        index=True,
    )

    #
    #
    # Payment term and Payment mode
    #
    payment_mode_id = fields.Many2one(
        comodel_name='account.payment.mode',
        string="Payment Mode",
    )
    # Este campo esta sendo inserido somente para fins gerenciais e não será
    # exibido na visão por enquanto.
    # TODO: Implementar um relatório que proporcione informações sobre o
    # ganho associado a diferentes condições de pagamentos.
    #
    payment_term_id = fields.Many2one(
        comodel_name='account.payment.term',
        string="Payment term",
    )

    document_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.document'
    )
    financial_account_id = fields.Many2one(
        comodel_name='financial.account',
    )

    # arrears_days = fields.Integer(
    #     string='Arrears Days',
    #     compute='_compute_arrears_days',
    #     store=True
    # )

    def generate_move(self, move_lines):
        for record in self:
            if record.amount:
                data = {
                    'name': '/',
                    'debit': record.amount,
                    # 'currency_id':
                    #     record.currency_id and record.currency_id.id or False,
                    'partner_id': record.partner_id and record.partner_id.id or False,
                    'account_id': record.partner_id.property_account_receivable_id.id,
                    'date_maturity': record.date_maturity,
                    'financial_payment_id': record.id,
                }
                move_lines.append((0, 0, data))
