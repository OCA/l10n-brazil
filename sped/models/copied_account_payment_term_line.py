# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia
#   Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#


from odoo import api, fields, models
from odoo.exceptions import ValidationError
import odoo.addons.decimal_precision as dp


class AccountPaymentTermLine(models.Model):
    _name = 'account.payment.term.line'
    _description = 'Payment Term Line'
    _order = 'sequence, id'

    TYPE = [
        ('balance', 'Balance'),
        ('percent', 'Percent'),
        ('fixed', 'Fixed Amount'),
    ]

    OPTIONS = [
        ('day_after_invoice_date', 'Day(s) after the invoice date'),
        ('fix_day_following_month',
         'Day(s) after the end of the invoice month (Net EOM)'),
        ('last_day_following_month', 'Last day of following month'),
        ('last_day_current_month', 'Last day of current month'),
    ]

    value = fields.Selection(
        selection=TYPE,
        string='Type',
        required=True,
        default='balance',
        help='Select here the kind of valuation related to this payment term '
             'line.',
    )
    value_amount = fields.Float(
        string='Value',
        digits=dp.get_precision('Payment Terms'),
        help='For percent enter a ratio between 0-100.',
    )
    days = fields.Integer(
        string='Number of Days',
        required=True,
        default=0,
    )
    option = fields.Selection(
        selection=OPTIONS,
        string='Options',
        default='day_after_invoice_date',
        required=True,
    )
    payment_id = fields.Many2one(
        comodel_name='account.payment.term',
        string='Payment Terms',
        required=True,
        index=True,
        ondelete='cascade',
    )
    sequence = fields.Integer(
        default=10,
        help='Gives the sequence order when displaying a list of payment term '
             'lines.',
    )

    @api.constrains('value', 'value_amount')
    def _check_percent(self):
        self.ensure_one()

        if (self.value == 'percent' and
            (self.value_amount < 0.0 or
             self.value_amount > 100.0)):
            raise ValidationError(_('Percentages for Payment Terms Line must '
                                    'be between 0 and 100.'))

    @api.onchange('option')
    def _onchange_option(self):
        if self.option in ('last_day_current_month',
                           'last_day_following_month'):
            self.days = 0
