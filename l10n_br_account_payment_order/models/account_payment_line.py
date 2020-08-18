# Copyright (C) 2016-Today - KMEE (<http://kmee.com.br>).
#  Luis Felipe Miléo - mileo@kmee.com.br
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.addons import decimal_precision as dp
from odoo.tools.float_utils import float_round as round # TODO check round methods in 12.0


class PaymentLine(models.Model):
    _inherit = 'account.payment.line'

    @api.multi
    @api.depends('percent_interest', 'amount_currency')
    def _compute_interest(self):
        for record in self:
            precision = record.env[
                'decimal.precision'].precision_get('Account')
            record.amount_interest = round(
                record.amount_currency * (
                    record.percent_interest / 100), precision)

    linha_digitavel = fields.Char(
        string='Linha Digitável',
    )

    percent_interest = fields.Float(
        string='Percentual de Juros',
        digits=dp.get_precision('Account'),
    )

    amount_interest = fields.Float(
        string='Valor Juros',
        compute='_compute_interest',
        digits=dp.get_precision('Account'),
    )
