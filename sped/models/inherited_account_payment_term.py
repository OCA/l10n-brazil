# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia
#   Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#


from odoo import api, fields, models
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta
from pybrasil.valor.decimal import Decimal as D
from ..constante_tributaria import *


class AccountPaymentTerm(models.Model):
    _inherit = 'account.payment.term'
    _rec_name = 'comercial_name'
    _order = 'sequence, name'

    sequence = fields.Integer(
        default=10,
    )
    is_installment_plan = fields.Boolean(
        string=u'Is monthly installment plan?',
        default=True,
    )
    has_down_payment = fields.Boolean(
        string=u'Has down payment?',
    )
    months = fields.Integer(
        string=u'Months',
    )
    # postpone_date_holiday = fields.Boolean(
    #     string=u'Postpone dates to next work day when holiday?',
    # )
    forma_pagamento = fields.Selection(
        selection=FORMA_PAGAMENTO,
        string=u'Forma de pagamento',
    )
    bandeira_cartao = fields.Selection(
        selection=BANDEIRA_CARTAO,
        string=u'Bandeira do cartão',
    )
    integracao_cartao = fields.Selection(
        selection=INTEGRACAO_CARTAO,
        string=u'Integração do cartão',
        default=INTEGRACAO_CARTAO_NAO_INTEGRADO,
    )
    participante_id = fields.Many2one(
        string=u'Operadora do cartão',
        ondelete='restrict',
    )
    comercial_name = fields.Char(
        string=u'Payment Terms',
        compute='_compute_comercial_name',
    )


    @api.multi
    def _compute_comercial_name(self):
        if self.env.context.get('currency_id'):
            currency = self.env['res.currency'].browse(
                self.env.context['currency_id'])
        else:
            currency = self.env.user.company_id.currency_id

        prec = D(10) ** (D(currency.decimal_places or 2) * -1)

        if self.env.context.get('lang'):
            lang = self.env['res.lang']._lang_get(self.env.context.get('lang'))
        else:
            lang = self.env['res.lang']._lang_get('en')

        value = D(self.env.context.get('value') or 0)

        for payment_term in self:
            comercial_name = u''
            if payment_term.forma_pagamento in FORMA_PAGAMENTO_CARTOES:
                if payment_term.forma_pagamento == \
                    FORMA_PAGAMENTO_CARTAO_CREDITO:
                    comercial_name += u'[Crédito '
                elif payment_term.forma_pagamento == \
                    FORMA_PAGAMENTO_CARTAO_DEBITO:
                    comercial_name += u'[Débito '

                comercial_name += \
                    BANDEIRA_CARTAO_DICT[payment_term.bandeira_cartao]
                comercial_name += u'] '

            elif payment_term.forma_pagamento:
                comercial_name += u'['
                comercial_name += \
                    FORMA_PAGAMENTO_DICT[payment_term.forma_pagamento]
                comercial_name += u'] '

            comercial_name += payment_term.name

            if payment_term.is_installment_plan and value > 0:
                comercial_name += ' de '
                comercial_name += currency.symbol
                comercial_name += u' '
                installment_amount = value / D(payment_term.months or 1)
                installment_amount = installment_amount.quantize(prec)
                comercial_name += lang.format('%.2f', installment_amount, True,
                                              True)

            payment_term.comercial_name = comercial_name

    def compute(self, value, date_ref=False):
        self.ensure_one()

        if not self.is_installment_plan:
            return super(AccountPaymentTerm, self).compute(value,
                                                           date_ref=date_ref)

        date_ref = date_ref or fields.Date.today()
        value = D(value)
        months = D(self.months or 1)
        res = []

        if self.env.context.get('currency_id'):
            currency = self.env['res.currency'].browse(
                self.env.context['currency_id'])
        else:
            currency = self.env.user.company_id.currency_id

        prec = D(10) ** (D(currency.decimal_places or 2) * -1)

        installment_amount = value / months
        installment_amount = installment_amount.quantize(prec)
        diff = value - (installment_amount * months)

        for i in range(months):
            next_date = fields.Date.from_string(date_ref)

            if self.has_down_payment:
                next_date += relativedelta(months=i)

            else:
                next_date += relativedelta(months=i + 1)

            installment = [
                fields.Date.to_string(next_date),
                installment_amount,
            ]

            if i == 0 and diff > 0:
                installment[1] += diff
                diff = 0

            elif i + 1 == months and diff != 0:
                installment[1] += diff

            res.append(installment)

        return res
