# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class FinancialMove(models.Model):

    _name = 'financial.move'
    _description = 'Financial Move'
    _inherit = ['mail.thread', 'financial.move.model']
    _order = "business_due_date desc, " \
             "ref desc, ref_item desc, document_number, id desc"
    _rec_name = 'ref'

    @api.multi
    @api.depends('ref', 'ref_item')
    def _compute_display_name(self):
        for record in self:
            if record.ref_item:
                record.display_name = record.ref + '/' + record.ref_item
            else:
                record.display_name = record.ref or ''

    @api.model
    def _avaliable_transition(self, old_state, new_state):
        allowed = [
            ('draft', 'open'),
            ('open', 'paid'),
            ('open', 'cancel'),
        ]
        return (old_state, new_state) in allowed

    ref = fields.Char(
        string='Ref',
        required=True,
        copy=False,
        readonly=True,
        states={'draft': [('readonly', False)]},
        index=True,
        default=lambda self: _('New')
    )
    ref_item = fields.Char(
        string=u"ref item",
        required=True,
        readonly=True,
        states={'draft': [('readonly', False)]},
    )
    display_name = fields.Char(
        string='Financial Reference',
        compute='_compute_display_name',
    )
    active = fields.Boolean(
        string=u'Active',
        default=True,
        track_visibility='onchange',
    )
    analytic_account_id = fields.Char()  # FIXME .Many2one(
    #
    # )
    account_account_id = fields.Char()  # FIXME .Many2one(
    #
    # )
    balance = fields.Monetary(
        compute='_compute_balance',
        track_visibility='onchange',
    )
    account = fields.Char()
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
        readonly=True,
    )
    change_reason = fields.Text(
        string="Change reason",
        track_visibility='onchange',
    )
    # partner_bank_id = fields.Many2one(
    #     comodel_name='res.partner.bank',
    # )
    # move_type = fields.Char()  # FIXME:

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
    @api.depends('related_payment_ids', 'amount_document')
    def _compute_balance(self):
        for record in self:
            if record.move_type in ('p', 'r'):
                balance = record.amount_document
                for payment in record.related_payment_ids:
                    balance -= (payment.amount_document +
                                payment.amount_discount -
                                payment.amount_interest -
                                payment.amount_delay_fee)
                record.balance = balance
            if record.balance <= 0 and record.related_payment_ids \
                    and record.state == 'open':
                record.change_state('paid')

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            if vals.get('move_type') == 'r':
                vals['ref'] = self.env['ir.sequence'].next_by_code(
                    'financial.move.receivable') or 'New'
                if not vals.get('ref_item'):
                    vals['ref_item'] = '1'
            elif vals.get('move_type') == 'p':
                vals['ref'] = self.env['ir.sequence'].next_by_code(
                    'financial.move.payable') or 'New'
                if not vals.get('ref_item'):
                    vals['ref_item'] = '1'
            else:
                pass
                # FIXME: For rr and pp
        result = super(FinancialMove, self).create(vals)
        return result
