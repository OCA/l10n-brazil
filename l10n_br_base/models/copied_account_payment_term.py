# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia
#   Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#


from odoo import api, fields, models
from odoo.exceptions import ValidationError


class AccountPaymentTerm(models.Model):
    _name = "account.payment.term"
    _description = "Payment Term"
    _order = "name"

    def _default_line_ids(self):
        return [(0, 0,
                 {
                     'value': 'balance',
                     'value_amount': 0.0,
                     'sequence': 9,
                     'days': 0,
                     'option': 'day_after_invoice_date'
                 })]

    name = fields.Char(
        string='Payment Terms',
        translate=True,
        required=True,
    )
    active = fields.Boolean(
        default=True,
        help="If the active field is set to False, it will allow you to hide "
             "the payment term without removing it.",
    )
    note = fields.Text(
        string='Description on the Invoice',
        translate=True,
    )
    line_ids = fields.One2many(
        comodel_name='account.payment.term.line',
        inverse_name='payment_id',
        string='Terms',
        copy=True,
        default=_default_line_ids,
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.user.company_id,
    )

    @api.constrains('line_ids')
    @api.one
    def _check_lines(self):
        payment_term_lines = self.line_ids.sorted()

        if payment_term_lines and payment_term_lines[-1].value != 'balance':
            raise ValidationError(_('A Payment Term should have its last line '
                                    'of type Balance.'))

        lines = self.line_ids.filtered(lambda r: r.value == 'balance')

        if len(lines) > 1:
            raise ValidationError(_('A Payment Term should have only one line '
                                    'of type Balance.'))

    @api.one
    def compute(self, value, date_ref=False):
        date_ref = date_ref or fields.Date.today()
        amount = value
        result = []

        if self.env.context.get('currency_id'):
            currency = self.env['res.currency'].browse(
                self.env.context['currency_id'])
        else:
            currency = self.env.user.company_id.currency_id

        prec = currency.decimal_places
        for line in self.line_ids:
            if line.value == 'fixed':
                amt = round(line.value_amount, prec)
            elif line.value == 'percent':
                amt = round(value * (line.value_amount / 100.0), prec)
            elif line.value == 'balance':
                amt = round(amount, prec)
            if amt:
                next_date = fields.Date.from_string(date_ref)
                if line.option == 'day_after_invoice_date':
                    next_date += relativedelta(days=line.days)
                elif line.option == 'fix_day_following_month':
                    # Getting 1st of next month
                    next_first_date = next_date + relativedelta(
                        day=1,
                        months=1,
                    )
                    next_date = next_first_date + relativedelta(
                        days=line.days - 1
                    )
                elif line.option == 'last_day_following_month':
                    # Getting last day of next month
                    next_date += relativedelta(day=31, months=1)
                elif line.option == 'last_day_current_month':
                    # Getting last day of next month
                    next_date += relativedelta(day=31, months=0)
                result.append((fields.Date.to_string(next_date), amt))
                amount -= amt

        amount = reduce(lambda x, y: x + y[1], result, 0.0)

        dist = round(value - amount, prec)
        if dist:
            last_date = result and result[-1][0] or fields.Date.today()
            result.append((last_date, dist))

        return result
