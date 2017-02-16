# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _
from odoo.exceptions import UserError

FINANCIAL_TYPE = [
    ('r', u'Account Receivable'),
    ('rr', u'Receipt'),
    ('p', u'Account Payable'),
    ('pp', u'Payment'),
    # ('in', u'Money in'),
    # ('out', u'Recieve'),
    # ('trans', u'Transfer'),
]

FINANCIAL_STATE = [
    ('draft', u'Draft'),
    ('budget', u'Budget'),
    ('open', u'Open'),
    ('paid', u'Paid'),
    ('cancel', u'Cancel'),
]


class FinancialMove(models.Model):

    _name = 'financial.move'
    _description = 'Financial Move'  # TODO
    _inherit = ['mail.thread']
    _order = "business_due_date desc, document_number desc, id desc"  # TODO:

    @api.model
    def _avaliable_transition(self, old_state, new_state):
        allowed = [
            ('draft', 'budget'),
            ('budget', 'open'),
            ('draft', 'open'),
            ('open', 'paid'),
            ('budget', 'paid'),
            ('budget', 'cancel'),  # TODO:
            ('open', 'cancel'),  # TODO:
        ]
        return (old_state, new_state) in allowed

    @api.multi
    @api.depends('due_date')
    def _compute_business_due_date(self):
        for record in self:
            if record.due_date:
                record.business_due_date = self.env[
                    'resource.calendar'].proximo_dia_util(
                    fields.Date.from_string(record.due_date))


    ref = fields.Char()
    move_type = fields.Selection(
        selection=FINANCIAL_TYPE,
    )
    state = fields.Selection(
        selection=FINANCIAL_STATE,
        string='Status',
        index=True,
        readonly=True,
        default='draft',
        track_visibility='onchange',
        copy=False,
    )
    active = fields.Boolean(
        string=u'Active',
        default=True,
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string=u'Company',
        required=True,
    )
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Currency',
        required=True,
    )
    payment_mode = fields.Many2one(
       comodel_name='payment.mode'
    )
    analytic_account_id = fields.Char()  # FIXME .Many2one(
    #
    # )
    account_account_id = fields.Char()  # FIXME .Many2one(
    #
    # )
    partner_id = fields.Many2one(
        comodel_name='res.partner',
    )
    # partner_bank_id = fields.Many2one(
    #     comodel_name='res.partner.bank',
    # )
    # move_type = fields.Char()  # FIXME:
    document_number = fields.Char()  # FIXME:
    document_date = fields.Date()  # FIXME: Data do documento ou
    # create_date = fields.Date()  # FIXME: Criação lançamento financeiro?
    # write_date = fields.Date() # Data de alteração
    amount_document = fields.Monetary()
    balance = fields.Monetary(
        compute='_compute_balance'
    )
    account = fields.Char()
    historic = fields.One2many(
        comodel_name='financial.move.history',
        inverse_name='financial_move_id',
    )
    due_date = fields.Date()
    business_due_date = fields.Date(
        string='Business due date',
        compute='_compute_business_due_date',
        store=True,
        index=True,
    )
    payment_date = fields.Date()
    credit_debit_date = fields.Date()
    amount_payment = fields.Monetary()
    # percent_interest = fields.Float() #  TODO:
    amount_interest = fields.Monetary()
    # percent_discount = fields.Float() #  TODO:
    amount_discount = fields.Monetary()
    amount_delay_fee = fields.Monetary()
    amount_residual = fields.Monetary()
    expected_date = fields.Date()  # TODO: Data prevista
    storno = fields.Boolean(
        string=u'Storno',
        readonly=True
    )
    printed = fields.Boolean(
        string=u'Printed',
        readonly=True
    )
    sent = fields.Boolean(
        string=u'Sent',
        readonly=True
    )
    regociated = fields.Boolean()
    regociated_id = fields.Many2one(
        comodel_name='financial.move',
    )
    related_regociated_ids = fields.One2many(
        comodel_name='financial.move',
        inverse_name='regociated_id',
    )
    payment_id = fields.Many2one(
        comodel_name='financial.move',
    )
    related_payment_ids = fields.One2many(
        comodel_name='financial.move',
        inverse_name='payment_id',
        readonly=False,
    )

    @api.multi
    def change_state(self, new_state):
        for record in self:
            if record._avaliable_transition(record.state, new_state):
                record.state = new_state
            else:
                raise UserError(_("This state transition is not allowed"))

    @api.multi
    def action_confirm(self):
        for record in self:
            record.change_state('open')

    @api.multi
    def action_budget(self):
        for record in self:
            record.change_state('budget')

    @api.multi
    def action_paid(self):
        for record in self:
            record.change_state('paid')

    @api.multi
    def action_cancel(self):
        for record in self:
            record.change_state('cancel')

    @api.multi
    @api.depends('amount_discount', 'related_payment_ids')
    def _compute_balance(self):
        for record in self:
            if record.move_type in ('p', 'r'):
                balance = record.amount_document
                for payment in record.related_payment_ids:
                    balance -= (payment.amount_document + payment.amount_discount -
                                payment.amount_interest - payment.amount_delay_fee)
                    #conferir variaveis
                record.balance = balance
                if balance <= 0:
                    record.change_state('paid')

