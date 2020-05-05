# Copyright 2020 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class AccountPaymentTermLine(models.Model):
    """ This code is a copy of account.payment.term.line with the same
    table name"""

    _name = "l10n_br_fiscal.payment.term.line"
    _table = 'account_payment_term_line'
    _description = "Payment Terms Line"
    _order = "sequence, id"

    value = fields.Selection([
        ('balance', 'Balance'),
        ('percent', 'Percent'),
        ('fixed', 'Fixed Amount')
    ], string='Type', required=True, default='balance',
        help="Select here the kind of valuation related to this payment terms line.")
    value_amount = fields.Float(string='Value',
                                help="For percent enter a ratio between 0-100.")
    days = fields.Integer(string='Number of Days', required=True, default=0)
    day_of_the_month = fields.Integer(
        string='Day of the month',
        help="Day of the month on which the invoice must come "
             "to its term. If zero or negative, this value will "
             "be ignored, and no specific day will be set. If"
             " greater than the last day of a month, "
             "this number will instead select the last day of this month.")
    option = fields.Selection([
        ('day_after_invoice_date', "day(s) after the invoice date"),
        ('after_invoice_month', "day(s) after the end of the invoice month"),
        ('day_following_month', "of the following month"),
        ('day_current_month', "of the current month"),
    ],
        default='day_after_invoice_date', required=True, string='Options'
    )
    payment_id = fields.Many2one(
        'l10n_br_fiscal.payment.term',
        string='Payment Terms',
        required=True, index=True, ondelete='cascade')
    sequence = fields.Integer(
        default=10,
        help="Gives the sequence order when displaying a list of payment terms lines.")

    @api.one
    @api.constrains('value', 'value_amount')
    def _check_percent(self):
        if self.value == 'percent' and (
                self.value_amount < 0.0 or self.value_amount > 100.0):
            raise ValidationError(
                _('Percentages on the Payment Terms lines must be between 0 and 100.'))

    @api.one
    @api.constrains('days')
    def _check_days(self):
        if self.option in (
                'day_following_month', 'day_current_month') and self.days <= 0:
            raise ValidationError(
                _("The day of the month used for this term must be stricly positive."))
        elif self.days < 0:
            raise ValidationError(
                _("The number of days used for a payment term cannot be negative."))

    @api.onchange('option')
    def _onchange_option(self):
        if self.option in ('day_current_month', 'day_following_month'):
            self.days = 0
