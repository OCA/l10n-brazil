# -*- coding: utf-8 -*-
##############################################################################
#
#    Account Payment Boleto module for Odoo
#    Copyright (C) 2012-2015 KMEE (http://www.kmee.com.br)
#    @author Luis Felipe Miléo <mileo@kmee.com.br>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from datetime import datetime, date
import logging
from openerp.addons.financial.constants import (
    FINANCIAL_DEBT_2RECEIVE,
    FINANCIAL_DEBT_2PAY
)

_logger = logging.getLogger(__name__)

try:
    from pyboleto.bank import BoletoException
    from pyboleto.bank.bancodobrasil import BoletoBB
    from pyboleto.bank.banrisul import BoletoBanrisul
    from pyboleto.bank.bradesco import BoletoBradesco
    from pyboleto.bank.caixa import BoletoCaixa
    from pyboleto.bank.caixa_sigcb import BoletoCaixaSigcb
    from pyboleto.bank.caixa_sindicato import BoletoCaixaSindicato
    from pyboleto.bank.hsbc import BoletoHsbc
    from pyboleto.bank.itau import BoletoItau
    from pyboleto.bank.santander import BoletoSantander

    from pybrasil.data import parse_datetime, hoje
    from pybrasil.valor.decimal import Decimal
    from pybrasil.inscricao import limpa_formatacao

except ImportError as err:
    _logger.debug = err


try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO



class BoletoOdoo(object):
    def __init__(self, financial_move, nosso_numero):
        self.nosso_numero = nosso_numero
        self.financial_move = financial_move

    def _instancia_boleto(self):
        banco = self._payment_mode.bank_id.bank.bic
        carteira = self._payment_mode.boleto_carteira
        convenio = self._payment_mode.convenio

        self.boleto = None

        if banco == '001':
            #
            # O banco do Brasil tem algumas configurações a mais, dependendo
            # do nº de dígitos do convênio
            #
            # Size of convenio 4, 6, 7 or 8
            # Nosso Numero format. 1 or 2
            # Used only for convenio=6
            # 1: Nosso Numero with 5 positions
            # 2: Nosso Numero with 17 positions
            tam_convenio = len(convenio or '')
            self.boleto = BoletoBB(tam_convenio, 2)

        elif banco == '041':
            self.boleto = BoletoBanrisul()

        elif banco == '237':
            self.boleto = BoletoBradesco()

        elif banco == '104':
            if carteira == 'Sigcb':
                self.boleto = BoletoCaixaSigcb()
            elif carteira == 'SIND':
                self.boleto = BoletoCaixaSindicato()
            else:
                self.boleto = BoletoCaixa()

        elif banco == '399':
            self.boleto = BoletoHsbc()

        elif banco == '341':
            self.boleto = BoletoItau()

        elif banco == '033':
            self.boleto = BoletoSantander()

        if self.boleto is None:
            raise BoletoException('Este banco não é suportado.')

    def set_payment_mode(self, payment_mode):
        self._payment_mode = payment_mode
        self._bank = payment_mode.bank_id
        self._instancia_boleto()

        self.boleto.agencia_beneficiario = self._bank.bra_number
        self.boleto.agencia_beneficiario_digito = \
            self._bank.bra_number_dig or ''

        self.boleto.convenio = self._payment_mode.convenio
        self.boleto.aceite = self._payment_mode.boleto_aceite
        self.boleto.carteira = self._payment_mode.boleto_carteira
        self.boleto.nosso_numero = self.nosso_numero

        #
        # Caso haja um código de beneficiário específico na carteira, usamos
        # este no lugar da conta
        #
        if self._payment_mode.beneficiario_codigo:
            self.boleto.conta_cedente = \
                self._payment_mode.beneficiario_codigo
            self.boleto.conta_cedente_digito = \
                self._payment_mode.beneficiario_digito or ''

        else:
            self.boleto.conta_cedente = self._bank.acc_number
            self.boleto.conta_cedente_digito = \
                self._bank.acc_number_dig or ''

        #
        # O beneficiário é sempre o dono da conta bancária vinculada à carteira
        #
        self.beneficiario = self._bank.partner_id

    def get_payment_mode(self):
        return self._payment_mode

    payment_mode = property(get_payment_mode, set_payment_mode)

    def set_financial_move(self, financial_move):
        self.payment_mode = financial_move.payment_mode_id

        self._financial_move = financial_move

        #
        # O pagador é o cliente quando o lançamento é a receber, e a empresa
        # quanto o lançamento é a pagar
        #
        if financial_move.type == FINANCIAL_DEBT_2RECEIVE:
            self.pagador = self._financial_move.partner_id
        elif financial_move.type == FINANCIAL_DEBT_2PAY:
            self.pagador = self._financial_move.company_id

        #
        # A data de vencimento é a data mesmo, e não a data útil
        #
        if self._financial_move.date_maturity:
            self.boleto.data_vencimento = \
                parse_datetime(self._financial_move.date_maturity).date()

        if self._financial_move.date_document:
            self.boleto.data_documento = \
                parse_datetime(self._financial_move.date_document).date()

        #
        # Usamos a função hoje da pybrasil para retornar a data considerando
        # *sempre* o fuso horário de Brasília, mesmo que os boletos sejam
        # gerados depois da 9 da noite (quando o UTC já vira a data pro dia
        # seguinte)
        # 
        self.boleto.data_processamento = hoje()
        self.boleto.valor = Decimal(financial_move.amount_document)
        self.boleto.valor_documento = Decimal(financial_move.amount_document)
        
        #
        # A espécie deve ser *sempre* reais, independente da moeda do 
        # lançamento financeiro; transferências em moeda estrangeiras usam
        # outro campo do CNAB, e não existem boletos que não sejam em reais
        #
        # self.boleto.especie = (
        #     financial_move.currency_id and
        #     financial_move.currency_id.symbol or 'R$')
        self.boleto.quantidade = ''
        
        self.boleto.numero_documento = self._financial_move.document_number

        #
        # A carteira de sindicato usa o tipo de serviço GRCSU
        #
        if self.boleto.carteira == 'SIND':
            self.boleto.especie_documento = 'GRCSU'

        else:
            self.boleto.especie_documento = \
                self._financial_move.document_type_id.boleto_especie

        instrucoes = []
        if financial_move.amount_paid_interest:
            instrucoes.append('mensagem com juros')
        if financial_move.payment_mode_id.bank_id.bank_bic == 104:
            instrucoes.append(
                "SAC CAIXA: 0800 726 0101 (informações, reclamações, sugestões"
                " e elogios) Para pessoas com deficiência auditiva ou de fala:"
                " 0800 726 2492 o Ouvidoria: 0800 725 7474 o caixa.gov.br")
        self.boleto.instrucoes = instrucoes

    def get_financial_move(self):
        return self._financial_move

    financial_move = property(get_financial_move, set_financial_move)

    def set_beneficiario(self, beneficiario):
        self._beneficiario = beneficiario
        
        self.boleto.cedente = self._beneficiario.legal_name \
            if self._beneficiario.legal_name else ''
        self.boleto.cedente_documento = self._beneficiario.cnpj_cpf \
            if self._beneficiario.cnpj_cpf else ''
        self.boleto.cedente_bairro = self._beneficiario.district or ''
        self.boleto.cedente_cep = self._beneficiario.zip or ''
        self.boleto.cedente_cidade = self._beneficiario.city or ''
        self.boleto.cedente_logradouro = (self._beneficiario.street or) '' + \
            ', ' + (self._beneficiario.number or 'SN')
        self.boleto.cedente_uf = self._beneficiario.state_id.code or ''

    def get_beneficiario(self):
        return self._beneficiario
    
    beneficiario = property(get_beneficiario, set_beneficiario)

    def set_pagador(self, pagador):
        self._pagador = pagador
        
        self.boleto.sacado_endereco = self._pagador.street + ', ' + (
            self._pagador.number or 'SN')
        self.boleto.sacado_cidade = self._pagador.city
        self.boleto.sacado_bairro = self._pagador.district
        self.boleto.sacado_uf = self._pagador.state_id.code
        self.boleto.sacado_cep = self._pagador.zip
        self.boleto.sacado_nome = self._pagador.legal_name \
            if self._pagador.legal_name else ''
        self.boleto.sacado_documento = self._pagador.cnpj_cpf

    def get_pagador(self):
        return self._pagador

    pagador = property(get_pagador, set_pagador)

    def set_cnae(self, cnae):
        self._cnae = limpa_formatacao(cnae)
        self.boleto.cnae = self._cnae

    def get_cnae(self):
        return self.cnae

    cnae = property(get_cnae, set_cnae)

    @classmethod
    def get_pdfs(cls, boleto_list):
        fbuffer = StringIO()

        fbuffer.reset()
        from pyboleto.pdf import BoletoPDF

        boleto = BoletoPDF(fbuffer)
        for i in range(len(boleto_list)):
            boleto.drawBoleto(boleto_list[i])
            boleto.nextPage()
        boleto.save()
        boleto_file = fbuffer.getvalue()

        fbuffer.close()
        return boleto_file

    @property
    def imagem_codigo_barras(self):
        self.boleto.imagem_codigo_barras
