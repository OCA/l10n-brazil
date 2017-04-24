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
    FORMA_PAGAMENTO_OUTROS,
    FORMA_PAGAMENTO_DICT,
    BANDEIRA_CARTAO_DICT,
)

_logger = logging.getLogger(__name__)

try:
    from pybrasil.valor.decimal import Decimal as D
    from pybrasil.data import (
        dia_util_pagamento,
        DIA_SEGUNDA, DIA_TERCA, DIA_QUARTA, DIA_QUINTA, DIA_SEXTA,
        primeiro_dia_mes, ultimo_dia_mes, dias_uteis,
    )

except (ImportError, IOError) as err:
    _logger.debug(err)


class AccountPaymentTerm(models.Model):
    _inherit = 'account.payment.term'
    _rec_name = 'nome_comercial'
    _order = 'sequence, name'

    DIAS_UTEIS = (
        (str(DIA_SEGUNDA), 'Segunda-feira'),
        (str(DIA_TERCA), 'Terça-feira'),
        (str(DIA_QUARTA), 'Quarta-feira'),
        (str(DIA_QUINTA), 'Quinta-feira'),
        (str(DIA_SEXTA), 'Sexta-feira'),
    )

    ADIA_ANTECIPA_DIA_UTIL = (
        ('P', 'Adia'),
        ('A', 'Antecipa'),
    )
    ADIA_DIA_UTIL = 'P'
    ANTECIPA_DIA_UTIL = 'A'

    DIAS_MES = (
        ('1', '1º'),
        #('2', '2'),
        #('3', '3'),
        #('4', '4'),
        ('5', '5'),
        #('6', '6'),
        #('7', '7'),
        #('8', '8'),
        #('9', '9'),
        ('10', '10'),
        #('11', '11'),
        #('12', '12'),
        #('13', '13'),
        #('14', '14'),
        ('15', '15'),
        #('16', '16'),
        #('17', '17'),
        #('18', '18'),
        #('19', '19'),
        ('20', '20'),
        #('21', '21'),
        #('22', '22'),
        #('23', '23'),
        #('24', '24'),
        ('25', '25'),
        #('26', '26'),
        #('27', '27'),
        #('28', '28'),
        #('29', '29'),
        ('30', '30'),
        #('31', '31'),
    )
    DIAS_MES_UTIL = (
        ('1', '1º'),
        #('2', '2º'),
        #('3', '3º'),
        #('4', '4º'),
        ('5', '5º'),
        #('6', '6º'),
        #('7', '7º'),
        #('8', '8º'),
        #('9', '9º'),
        ('10', '10º'),
        #('11', '11º'),
        #('12', '12º'),
        #('13', '13º'),
        #('14', '14º'),
        ('15', '15º'),
        #('16', '16º'),
        #('17', '17º'),
        #('18', '18º'),
        #('19', '19º'),
        ('20', '20º'),
    )

    sequence = fields.Integer(
        default=10,
    )
    em_parcelas_mensais = fields.Boolean(
        string='Em parcelas mensais?',
        default=True,
    )
    com_entrada = fields.Boolean(
        string='Com entrada?',
    )
    meses = fields.Integer(
        string='Meses',
    )
    somente_dias_uteis = fields.Boolean(
        string='Somente dias úteis?',
    )
    antecipa_dia_util = fields.Selection(
        selection=ADIA_ANTECIPA_DIA_UTIL,
        string='Adia ou antecipa dia útil?',
        default=ADIA_DIA_UTIL,
    )
    todo_dia_mes = fields.Selection(
        selection=DIAS_MES,
        string='Vencimento todo dia',
    )
    todo_dia_mes_util = fields.Selection(
        selection=DIAS_MES_UTIL,
        string='Vencimento todo dia útil',
    )
    evitar_dia_semana = fields.Selection(
        selection=DIAS_UTEIS,
        string='Evitar vencimento em',
    )
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

    def _verifica_dia_util(self, data):
        self.ensure_one()

        if self.somente_dias_uteis:
            if self.env.user.company_id.sped_empresa_id:
                empresa = self.env.user.company_id.sped_empresa_id
                if self.antecipa_dia_util == self.ANTECIPA_DIA_UTIL:
                    data = dia_util_pagamento(data, empresa.estado,
                                              empresa.cidade, antecipa=True)
                else:
                    data = dia_util_pagamento(data, empresa.estado,
                                              empresa.cidade)
            else:
                if self.antecipa_dia_util == self.ANTECIPA_DIA_UTIL:
                    data = dia_util_pagamento(data, antecipa=True)
                else:
                    data = dia_util_pagamento(data)

        if self.evitar_dia_semana and data.weekday() == \
            int(self.evitar_dia_semana):
            data += relativedelta(days=1)
            data = self._verifica_dia_util(data)

        return data

    def _verifica_dia_mes(self, data):
        self.ensure_one()

        if self.todo_dia_mes:
            data += relativedelta(day=int(self.todo_dia_mes))

        elif self.todo_dia_mes_util:
            if self.env.user.company_id.sped_empresa_id:
                empresa = self.env.user.company_id.sped_empresa_id
                dias = dias_uteis(primeiro_dia_mes(data), ultimo_dia_mes(data),
                                  empresa.estado, empresa.cidade)
            else:
                dias = dias_uteis(primeiro_dia_mes(data), ultimo_dia_mes(data))

            if int(self.todo_dia_mes_util) <= len(dias):
                data = dias[int(self.todo_dia_mes_util) - 1]

        return data

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

            if self.com_entrada:
                proxima_data += relativedelta(months=i)

            else:
                proxima_data += relativedelta(months=i + 1)

            proxima_data = self._verifica_dia_mes(proxima_data)
            proxima_data = self._verifica_dia_util(proxima_data)

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
