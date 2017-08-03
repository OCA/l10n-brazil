# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.tools import float_is_zero


class FinancialMove(models.Model):
    _inherit = b'financial.move'

    cheque_ids = fields.Many2many(
        comodel_name='financeiro.cheque',
        string=u'Cheques'
    )

    @api.multi
    @api.depends('state', 'currency_id', 'amount_total', 'cheque_ids.valor',
                 'cheque_ids.state')
    def _compute_residual(self):
        for record in self:
            amount_paid = 0.00
            if record.financial_type in ('2receive', '2pay'):  # FIXME
                for payment in record.related_payment_ids:
                    amount_paid += payment.amount_total
                for cheque in record.cheque_ids:
                    if cheque.state in ['descontado', 'repassado']:
                        amount_paid += cheque.valor
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
