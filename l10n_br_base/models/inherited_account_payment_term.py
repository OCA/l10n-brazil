# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia
#   Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from __future__ import division, print_function, unicode_literals

import logging

from odoo import api, fields, models
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta
from odoo.addons.l10n_br_base.constante_tributaria import (
    FORMA_PAGAMENTO,
    BANDEIRA_CARTAO,
    INTEGRACAO_CARTAO,
    INTEGRACAO_CARTAO_NAO_INTEGRADO,
    FORMA_PAGAMENTO_CARTOES,
    FORMA_PAGAMENTO_CARTAO_CREDITO,
    FORMA_PAGAMENTO_CARTAO_DEBITO,
    FORMA_PAGAMENTO_DICT,
    BANDEIRA_CARTAO_DICT,
)

_logger = logging.getLogger(__name__)

try:
    from pybrasil.valor.decimal import Decimal as D
    from pybrasil.data

except (ImportError, IOError) as err:
    _logger.debug(err)


class AccountPaymentTerm(models.Model):
    _inherit = 'account.payment.term'
    _rec_name = 'nome_comercial'
    _order = 'sequence, name'

    sequence = fields.Integer(
        default=10,
    )
    em_parcelas_mensais = fields.Boolean(
        string='Em parcelas mensais?',
        default=True,
    )
    tem_entrada = fields.Boolean(
        string='Tem entrada?',
    )
    meses = fields.Integer(
        string='Meses',
    )
    somente_dias_uteis = fields.Boolean(
        string='Somente dias úteis?',
    )
    forma_pagamento = fields.Selection(
        selection=FORMA_PAGAMENTO,
        string='Forma de pagamento',
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
    participante_id = fields.Many2one(
        string='Operadora do cartão',
        ondelete='restrict',
    )
    nome_comercial = fields.Char(
        string='Condição da pagamento',
        compute='_compute_nome_comercial',
    )

    @api.multi
    def _compute_nome_comercial(self):
        if self.env.context.get('currency_id'):
            currency = self.env['res.currency'].browse(
                self.env.context['currency_id'])
        else:
            currency = self.env.user.company_id.currency_id

        prec = D(10) ** (D(currency.decimal_places or 2) * -1)

        if self.env.context.get('lang'):
            lang = self.env['res.lang']._lang_get(self.env.context.get('lang'))
        else:
            lang = self.env['res.lang']._lang_get('pt_BR')

        valor = D(self.env.context.get('value') or 0)

        for payment_term in self:
            nome_comercial = ''
            if payment_term.forma_pagamento in FORMA_PAGAMENTO_CARTOES:
                if payment_term.forma_pagamento == \
                    FORMA_PAGAMENTO_CARTAO_CREDITO:
                    nome_comercial += '[Crédito '
                elif payment_term.forma_pagamento == \
                    FORMA_PAGAMENTO_CARTAO_DEBITO:
                    nome_comercial += '[Débito '

                nome_comercial += \
                    BANDEIRA_CARTAO_DICT[payment_term.bandeira_cartao]
                nome_comercial += '] '

            elif payment_term.forma_pagamento:
                nome_comercial += '['
                nome_comercial += \
                    FORMA_PAGAMENTO_DICT[payment_term.forma_pagamento]
                nome_comercial += '] '

            nome_comercial += payment_term.name

            if payment_term.em_parcelas_mensais and valor > 0:
                nome_comercial += ' de '
                nome_comercial += currency.symbol
                nome_comercial += ' '
                valor_parcela = valor / D(payment_term.meses or 1)
                valor_parcela = valor_parcela.quantize(prec)
                nome_comercial += lang.format('%.2f', valor_parcela, True,
                                              True)

            payment_term.nome_comercial = nome_comercial

    def compute(self, value, date_ref=False):
        self.ensure_one()

        if not self.em_parcelas_mensais:
            return super(AccountPaymentTerm, self).compute(value,
                                                           date_ref=date_ref)

        data_referencia = date_ref or fields.Date.today()
        valor = D(value)
        meses = D(self.meses or 1)
        res = []

        if self.env.context.get('currency_id'):
            currency = self.env['res.currency'].browse(
                self.env.context['currency_id'])
        else:
            currency = self.env.user.company_id.currency_id

        prec = D(10) ** (D(currency.decimal_places or 2) * -1)

        valor_parcela = valor / meses
        valor_parcela = valor_parcela.quantize(prec)
        diferenca = valor - (valor_parcela * meses)

        for i in range(meses):
            proxima_data = fields.Date.from_string(data_referencia)

            if self.tem_entrada:
                proxima_data += relativedelta(meses=i)

            else:
                proxima_data += relativedelta(meses=i + 1)

            if self.somente_dias_uteis:
                if self.env.user.company_id.sped_empresa_id:
                    empresa = self.env.user.company_id.sped_empresa_id
                    proxima_data = dia_util_pagamento(proxima_data,
                                                      empresa.estado,
                                                      empresa.cidade
                                                      )
                else:
                    proxima_data = dia_util_pagamento(proxima_data)

            parcela = [
                fields.Date.to_string(proxima_data),
                valor_parcela,
            ]

            if i == 0 and diferenca > 0:
                parcela[1] += diferenca
                diferenca = 0

            elif i + 1 == meses and diferenca != 0:
                parcela[1] += diferenca

            res.append(parcela)

        return res
