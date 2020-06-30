# Copyright 2020 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError, ValidationError


class FiscalPaymentTerm(models.Model):
    """ This code is a copy of account.payment.term, with the same table"""

    _name = 'l10n_br_fiscal.payment.term'
    _table = 'account_payment_term'

    _description = 'Fiscal Payment Term'
    _order = "sequence, id"

    def _default_line_ids(self):
        return [(0, 0, {
            'value': 'balance',
            'value_amount': 0.0,
            'sequence': 9,
            'days': 0,
            'option': 'day_after_invoice_date'
        })]

    name = fields.Char(string='Payment Terms', translate=True, required=True)
    active = fields.Boolean(
        default=True,
        help="If the active field is set to False, it will allow you to hide the"
             " payment terms without removing it.")
    note = fields.Text(string='Description on the Invoice', translate=True)
    line_ids = fields.One2many(
        'l10n_br_fiscal.payment.term.line',
        'payment_id',
        string='Terms',
        copy=True,
        default=_default_line_ids)
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True, default=lambda self: self.env.user.company_id)
    sequence = fields.Integer(required=True, default=10)

    @api.constrains('line_ids')
    @api.one
    def _check_lines(self):
        payment_term_lines = self.line_ids.sorted()
        if payment_term_lines and payment_term_lines[-1].value != 'balance':
            raise ValidationError(
                _('The last line of a Payment Term should have the Balance type.'))
        lines = self.line_ids.filtered(lambda r: r.value == 'balance')
        if len(lines) > 1:
            raise ValidationError(
                _('A Payment Term should have only one line of type Balance.'))

    @api.one
    def compute(self, value, date_ref=False):
        date_ref = date_ref or fields.Date.today()
        amount = value
        sign = value < 0 and -1 or 1
        result = []
        if self.env.context.get('currency_id'):
            currency = self.env['res.currency'].browse(self.env.context['currency_id'])
        else:
            currency = self.env.user.company_id.currency_id
        for line in self.line_ids:
            if line.value == 'fixed':
                amt = sign * currency.round(line.value_amount)
            elif line.value == 'percent':
                amt = currency.round(value * (line.value_amount / 100.0))
            elif line.value == 'balance':
                amt = currency.round(amount)
            if amt:
                next_date = fields.Date.from_string(date_ref)
                if line.option == 'day_after_invoice_date':
                    next_date += relativedelta(days=line.days)
                    if line.day_of_the_month > 0:
                        months_delta = \
                            (line.day_of_the_month < next_date.day) and 1 or 0
                        next_date += relativedelta(
                            day=line.day_of_the_month, months=months_delta)
                elif line.option == 'after_invoice_month':
                    next_first_date = next_date + relativedelta(
                        day=1, months=1)  # Getting 1st of next month
                    next_date = next_first_date + relativedelta(days=line.days - 1)
                elif line.option == 'day_following_month':
                    next_date += relativedelta(day=line.days, months=1)
                elif line.option == 'day_current_month':
                    next_date += relativedelta(day=line.days, months=0)
                result.append((fields.Date.to_string(next_date), amt))
                amount -= amt
        amount = sum(amt for _, amt in result)
        dist = currency.round(value - amount)
        if dist:
            last_date = result and result[-1][0] or fields.Date.today()
            result.append((last_date, dist))
        return result

    @api.multi
    def unlink(self):
        if self.env['l10n_br_fiscal.document'].search(
                [('payment_term_id', 'in', self.ids)]):
            raise UserError(_(
                'You can not delete payment terms as other '
                'records still reference it. However, you can archive it.'))
        if self.env['l10n_br_fiscal.payment'].search(
                [('payment_term_id', 'in', self.ids)]):
            raise UserError(_(
                'You can not delete payment terms as other'
                ' records still reference it. However, you can archive it.'))
        property_recs = self.env['ir.property'].search(
            [('value_reference', 'in', [
                'l10n_br_fiscal.payment.term,%s' % payment_term.id
                for payment_term in self])
             ])
        property_recs.unlink()
        return super(FiscalPaymentTerm, self).unlink()
