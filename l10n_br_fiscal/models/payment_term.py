# Copyright 2020 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _
from dateutil.relativedelta import relativedelta

from ..constants.payment import (
    BANDEIRA_CARTAO,
    FORMA_PAGAMENTO,
    INTEGRACAO_CARTAO,
    INTEGRACAO_CARTAO_NAO_INTEGRADO,
    FORMA_PAGAMENTO_OUTROS,
)


class FiscalPaymentTermAbstract(models.Model):

    _name = 'l10n_br_fiscal.payment.term.abstract'

    forma_pagamento = fields.Selection(
        selection=FORMA_PAGAMENTO,
        string='Forma de pagamento',
        default=FORMA_PAGAMENTO_OUTROS,
    )
    bandeira_cartao = fields.Selection(
        selection=BANDEIRA_CARTAO,
        string='Bandeira do cartão',
    )
    integracao_cartao = fields.Selection(
        selection=INTEGRACAO_CARTAO,
        string='Integração do cartão',
        default=INTEGRACAO_CARTAO_NAO_INTEGRADO,
    )
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Operadora do cartão',
        ondelete='restrict',
    )


class FiscalPaymentTerm(models.Model):

    _name = 'l10n_br_fiscal.payment.term'
    _inherit = 'l10n_br_fiscal.payment.term.abstract'
    _table = 'account_payment_term'

    _description = 'Fiscal Payment Term'
    _order = "sequence, id"

    name = fields.Char(string='Payment Terms', translate=True, required=True)
    sequence = fields.Integer(required=True, default=10)
    number_of_terms = fields.Integer(
        string="Número de parcelas",
        default=1
    )

    @api.one
    def compute(self, value, date_ref=False):
        date_ref = date_ref or fields.Date.today()
        amount = value

        result = []

        if not amount:
            return result

        if self.env.context.get('currency_id'):
            currency = self.env['res.currency'].browse(self.env.context['currency_id'])
        else:
            currency = self.env.user.company_id.currency_id

        for step in range(self.number_of_terms):
            amt = currency.round(value / self.number_of_terms)

            next_date = fields.Date.from_string(date_ref)
            next_date += relativedelta(month=1)

            result.append((fields.Date.to_string(next_date), amt))
            amount -= amt

        amount = sum(amt for _, amt in result)
        dist = currency.round(value - amount)
        if dist:
            last_date = result and result[-1][0] or fields.Date.today()
            result.append((last_date, dist))

        if not result:
            result.append((amount, date_ref))
        return result
