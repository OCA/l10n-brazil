# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import datetime

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_is_zero
from ..constants import (
    FINANCIAL_SEQUENCE,
)


class FinancialMove(models.Model):
    _name = 'financial.move'
    _description = 'Financial Move'
    _inherit = ['mail.thread', 'abstract.financial']
    _order = "date_business_maturity desc, " \
             "ref desc, ref_item desc, document_number, id desc"
    _rec_name = 'ref'

    @api.depends('amount',
                 'amount_interest',
                 'amount_discount',
                 'amount_refund',
                 'amount_cancel',
                 )
    def _compute_totals(self):
        for record in self:
            amount_total = (
                record.amount +
                record.amount_interest -
                record.amount_discount -
                record.amount_refund -
                record.amount_cancel
            )
            record.amount_total = amount_total

    @api.multi
    @api.depends('state', 'currency_id', 'amount_total',
                 'related_payment_ids.amount_total')
    def _compute_residual(self):
        for record in self:
            amount_paid = 0.00
            if record.financial_type in ('2receive', '2pay'):  # FIXME
                for payment in record.related_payment_ids:
                    amount_paid += payment.amount_total
                amount_residual = record.amount_total - amount_paid
                digits_rounding_precision = record.currency_id.rounding

                record.amount_residual = amount_residual
                record.amount_paid = amount_paid
                if float_is_zero(
                        amount_residual,
                        precision_rounding=digits_rounding_precision):
                    record.reconciled = True
                else:
                    record.reconciled = False

    @api.multi
    @api.depends('ref', 'ref_item')
    def _compute_display_name(self):
        for record in self:
            if record.ref_item:
                record.display_name = record.ref + '/' + record.ref_item
            else:
                record.display_name = record.ref or ''

    @api.multi
    @api.depends('date_maturity')
    def _compute_date_business_maturity(self):
        # TODO: refactory for global OCA use avoiding l10n_br_resource
        for record in self:
            if record.date_maturity:
                record.date_business_maturity = self.env[
                    'resource.calendar'].proximo_dia_util_bancario(
                    fields.Date.from_string(record.date_maturity))

    def _readonly_state(self):
        return {'draft': [('readonly', False)]}

    def _required_fields(self):
        return True

    def _track_visibility_onchange(self):
        return 'onchange'

    def _compute_search_filter(self):
        return self

    date_business_maturity_search = fields.Date(
        compute='_compute_search_filter',
        store=True,
    )
    date_issue_search = fields.Date(
        compute='_compute_search_filter',
        store=True,
    )
    partner_search = fields.Many2one(
        comodel_name='res.partner',
        compute='_compute_search_filter',
        store=True,
    )
    account_analytic_search = fields.Many2one(
        comodel_name='account.analytic.account',
        compute='_compute_search_filter',
        store=True,
    )
    payment_mode_search = fields.Many2one(
        comodel_name='account.payment.mode',
        compute='_compute_search_filter',
        store=True,
    )
    document_number_search = fields.Char(
        compute='_compute_search_filter',
        store=True,
    )
    document_item_search = fields.Char(
        compute='_compute_date_filter',
        store=True,
    )
    ref = fields.Char(
        required=True,
        copy=False,
        readonly=True,
        states=_readonly_state,
        index=True,
        default=lambda self: _(u'New')
    )
    ref_item = fields.Char(
        string=u"ref item",
        readonly=True,
        states=_readonly_state,
    )
    display_name = fields.Char(
        string=u'Financial Reference',
        compute='_compute_display_name',
    )
    date = fields.Date(
        string=u'Financial date',
        default=fields.Date.context_today,
    )
    date_maturity = fields.Date(
        string=u'Maturity date',
    )
    date_business_maturity = fields.Date(
        string=u'Business maturity',
        readonly=True,
        store=True,
        compute='_compute_date_business_maturity'
    )
    date_payment = fields.Date(
        string=u'Payment date',
        readonly=True,
        default=False,
    )
    date_credit_debit = fields.Date(
        string=u'Credit debit date',
        readonly=True,
    )
    amount_total = fields.Monetary(
        string=u'Total',
        readonly=True,
        compute='_compute_totals',
        store=True,
        index=True
    )
    amount_paid = fields.Monetary(
        string=u'Paid',
        readonly=True,
        compute='_compute_residual',
        store=True,
    )
    amount_discount = fields.Monetary(
        string=u'Discount',
    )
    amount_interest = fields.Monetary(
        string=u'Interest',
        readonly=True,
        compute='_compute_interest',
    )
    amount_refund = fields.Monetary(
        string=u'Refund',
        readonly=True,
    )
    amount_residual = fields.Monetary(
        string=u'Residual',
        readonly=True,
        compute='_compute_residual',
        store=True,
    )
    amount_cancel = fields.Monetary(
        string=u'Cancel',
        readonly=True,
    )
    related_payment_ids = fields.One2many(
        comodel_name='financial.move',
        inverse_name='financial_payment_id',
        readonly=True,
    )
    financial_payment_id = fields.Many2one(
        comodel_name='financial.move',
    )
    reconciled = fields.Boolean(
        string='Paid/Reconciled',
        store=True,
        readonly=True,
        compute='_compute_residual',
    )

    @api.multi
    @api.constrains('amount')
    def _check_amount(self):
        for record in self:
            if not record.amount > 0.0 and record.state not in 'cancel':
                raise ValidationError(_(
                    'The payment amount must be strictly positive.'
                ))

    @api.model
    def _avaliable_transition(self, old_state, new_state):
        allowed = [
            ('draft', 'open'),
            ('open', 'paid'),
            ('open', 'cancel'),
        ]
        return (old_state, new_state) in allowed

    @api.multi
    def action_number(self):
        for record in self:
            if record.ref == _(u'New'):
                sequencial_ids = self.search([
                    ('document_number', '=', record.document_number),
                ], order='date_business_maturity')
                if self.search_count([
                    ('document_number', '=', record.document_number),
                    ('ref', '=', _(u'New')),
                ]) == len(sequencial_ids.ids):
                    sequencial_ids.write({
                        'ref': self.env['ir.sequence'].next_by_code(
                            FINANCIAL_SEQUENCE[
                                record.financial_type]) or u'New'
                    })
                    for i, x in enumerate(sequencial_ids):
                        x.ref_item = i + 1

    def _before_create(self, values):
        return values

    @api.model
    def create(self, values):
        values = self._before_create(values)
        result = super(FinancialMove, self).create(values)
        return self._after_create(result)

    def _after_create(self, result):
        return result

    @api.multi
    def _write(self, vals):
        pre_not_reconciled = self.filtered(
            lambda financial: not financial.reconciled)
        pre_reconciled = self - pre_not_reconciled
        res = super(FinancialMove, self)._write(vals)
        reconciled = self.filtered(lambda financial: financial.reconciled)
        not_reconciled = self - reconciled
        (reconciled & pre_reconciled).filtered(
            lambda financial: financial.state == 'open').action_paid()
        (not_reconciled & pre_not_reconciled).filtered(
            lambda invoice: invoice.state == 'paid').action_estorno()
        return res

    @api.multi
    def unlink(self):
        for financial in self:
            if financial.state not in ('draft', 'cancel'):
                if financial.document_number:
                    # TODO: Improve this validation!
                    raise UserError(
                        _('You cannot delete an financial move which is \n'
                          'generated by another document \n'
                          'try to cancel you document first'))
                raise UserError(
                    _('You cannot delete an financial move which is not \n'
                      'draft or cancelled'))
        return super(FinancialMove, self).unlink()

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
        self.action_number()

    @api.multi
    def action_budget(self):
        for record in self:
            record.change_state('budget')

    @api.multi
    def action_paid(self):
        for record in self:
            record.change_state('paid')

    @api.multi
    def action_estorno(self):
        for record in self:
            record.change_state('open')

    @api.multi
    def action_cancel(self, reason):
        for record in self:
            record.change_state('cancel')
            if record.note:
                new_note = record.note + u'\nCancel reason: ' + reason
            else:
                new_note = u'Cancel reason: ' + reason
            record.write({
                'amount_cancel': record.amount,
                'note': new_note
            })

    @staticmethod
    def _prepare_financial_move(
            bank_id, company_id, currency_id,
            financial_type, partner_id, document_number,
            date, date_maturity, amount,
            analytic_account_id=False, account_type_id=False,
            payment_term_id=False, payment_mode_id=False,
            **kwargs):
        return dict(
            bank_id=bank_id,
            company_id=company_id,
            currency_id=currency_id,
            financial_type=financial_type,
            partner_id=partner_id,
            document_number=document_number,
            date=date,
            payment_mode_id=payment_mode_id,
            payment_term_id=payment_term_id,
            analytic_account_id=analytic_account_id,
            account_type_id=account_type_id,
            date_maturity=date_maturity,
            amount=amount,
            **kwargs
        )

    @api.multi
    def action_view_financial(self, financial_type):
        if financial_type == '2receive':
            action = self.env.ref(
                'financial.financial_receivable_act_window').read()[0]
        elif financial_type == '2pay':
            action = self.env.ref(
                'financial.financial_payable_act_window').read()[0]
        if len(self) > 1:
            action['domain'] = [('id', 'in', self.ids)]
        elif len(self) == 1:
            action['views'] = [
                (self.env.ref('financial.financial_move_form_view').id, 'form')
            ]
            action['res_id'] = self.ids[0]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action

    def cron_interest(self):
        if self.env['resource.calendar'].data_eh_dia_util_bancario(
                datetime.today()):
            record = self.search([
                ('state', '=', 'open'),
                ('date_business_maturity', '<', datetime.today())])
            record._compute_interest()

    @api.depends('payment_mode_id', 'amount', 'date_business_maturity')
    def _compute_interest(self):
        for record in self:
            if self.env['resource.calendar']. \
                    data_eh_dia_util_bancario(datetime.today()) and record. \
                    state == 'open' and \
                    (datetime.today() > datetime.strptime
                        (record.date_business_maturity, '%Y-%m-%d')):
                day = (
                    datetime.today() - datetime.strptime(
                        record.date_maturity,
                        '%Y-%m-%d'))
                interest = record.amount * (record.payment_mode_id.
                                            interest_percent * day.days) / 100

                delay_fee = (record.payment_mode_id.
                             delay_fee_percent / 100) * record.amount
                record.amount_interest = interest + delay_fee
        pass

    def create_contract(self, financial_create):
        financial_move = self.env['financial.move']
        for record in financial_create:
            for move in record.line_ids:
                kargs = {}
                values = self._prepare_financial_move(
                    bank_id=financial_create.bank_id.id,
                    company_id=financial_create.company_id.id,
                    currency_id=financial_create.currency_id.id,
                    financial_type=financial_create.financial_type,
                    partner_id=financial_create.partner_id.id,
                    document_number=move.document_item,
                    date=financial_create.date,
                    payment_mode_id=financial_create.payment_mode_id.id,
                    payment_term_id=financial_create.payment_term_id.id,
                    analytic_account_id=(
                        financial_create.analytic_account_id.id
                    ),
                    account_type_id=financial_create.account_type_id.id,
                    date_maturity=move.date_maturity,
                    amount=move.amount,
                    note=record.note,
                    **kargs
                )
                financial = self.create(values)
                financial.action_confirm()
                financial_move |= financial
        return financial_move
