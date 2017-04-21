# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia
#   Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from __future__ import division, print_function, unicode_literals

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
import odoo.addons.decimal_precision as dp


class AccountPaymentTermLine(models.Model):
    _name = b'account.payment.term.line'
    _description = 'Payment Term Line'
    _order = 'sequence, id'

    TYPE = [
        ('balance', u'Balance'),
        ('percent', u'Percent'),
        ('fixed', u'Fixed Amount'),
    ]

    OPTIONS = [
        ('day_after_invoice_date', u'Day(s) after the invoice date'),
        ('fix_day_following_month',
         u'Day(s) after the end of the invoice month (Net EOM)'),
        ('last_day_following_month', u'Last day of following month'),
        ('last_day_current_month', u'Last day of current month'),
    ]

    value = fields.Selection(
        selection=TYPE,
        string=u'Type',
        required=True,
        default='balance',
        help=u'Select here the kind of valuation related to this payment term '
             u'line.',
    )
    value_amount = fields.Float(
        string=u'Value',
        digits=dp.get_precision('Payment Terms'),
        help=u'For percent enter a ratio between 0-100.',
    )
    days = fields.Integer(
        string=u'Number of Days',
        required=True,
        default=0,
    )
    option = fields.Selection(
        selection=OPTIONS,
        string=u'Options',
        default='day_after_invoice_date',
        required=True,
    )
    payment_id = fields.Many2one(
        comodel_name='account.payment.term',
        string=u'Payment Terms',
        required=True,
        index=True,
        ondelete='cascade',
    )
    sequence = fields.Integer(
        default=10,
        help=u'Gives the sequence order when displaying a list of payment '
             u'term lines.',
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
