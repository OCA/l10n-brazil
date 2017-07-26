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
    from pyboleto import bank
except ImportError as err:
    _logger.debug = err


try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO
BoletoException = bank.BoletoException


class Boleto(object):
    account_number = ''
    account_digit = ''

    branch_number = ''
    branch_digit = ''

    nosso_numero = ''

    @staticmethod
    def getBoleto(financial_move, nosso_numero):
        payment_mode = financial_move.payment_mode_id
        carteira = payment_mode.boleto_carteira
        banco = payment_mode.bank_id.bank.bic

        result = False

        if banco == '001':
            result = BoletoBB
        elif banco == '041':
            result = BoletoBarisul
        elif banco == '237':
            result = BoletoBradesco
        elif banco == '104':
            if carteira == 'Sigcb':
                result = BoletoCaixaSigcb
            elif carteira in ['SR']:
                result = BoletoCaixa
        elif banco == '399':
            result = BoletoHsbc
        elif banco == '341':
            if carteira == '157':
                result = BoletoItau157
            elif carteira in ['175', '174', '178', '104', '109']:
                result = BoletoItau
        elif banco == '356':
            result = BoletoReal
        elif banco == '033':
            if carteira == '102':
                result = BoletoSantander102
            elif carteira in ['101', '201']:
                result = BoletoStatander101201

        if result:
            return result(financial_move, nosso_numero)
        else:
            raise (BoletoException('Este banco não é suportado.'))

    @staticmethod
    def getBoletoClass(financial_move):
        bank_code = financial_move.payment_mode_id.bank_id.bank.bic
        return bank.get_class_for_codigo(bank_code)

    def __init__(self, financial_move):
        cedente = financial_move.payment_mode_id.bank_id.partner_id
        if financial_move.type == FINANCIAL_DEBT_2RECEIVE:
            sacado = financial_move.partner_id
        elif financial_move.type == FINANCIAL_DEBT_2PAY:
            sacado = financial_move.company_id
        self._cedente(cedente)
        self._sacado(sacado)
        self._financial_move(financial_move)

        # self.nosso_numero = ''

    def getAccountNumber(self):
        if self.account_digit:
            return str(self.account_number + '-' +
                       self.account_digit).encode('utf-8')
        return self.account_number.encode('utf-8')

    def getBranchNumber(self):
        if self.branch_digit:
            return str(self.branch_number + '-' +
                       self.branch_digit).encode('utf-8')
        return self.branch_number.encode('utf-8')

    def _financial_move(self, financial_move):
        self._payment_mode(financial_move)
        self.boleto.data_vencimento = datetime.date(datetime.strptime(
            financial_move.date_business_maturity, '%Y-%m-%d'))
        self.boleto.data_documento = datetime.date(datetime.strptime(
            financial_move.date_document, '%Y-%m-%d'))
        self.boleto.data_processamento = date.today()
        self.boleto.valor = str("%.2f" % financial_move.amount_document)
        self.boleto.valor_documento = str("%.2f" %
                                          financial_move.amount_document)
        self.boleto.especie = (
            financial_move.currency_id and
            financial_move.currency_id.symbol or 'R$')
        self.boleto.quantidade = ''
        # str("%.2f" % financial_move.amount_currency)
        self.boleto.numero_documento = \
            financial_move.document_number.encode('utf-8')
        instrucoes = []
        if financial_move.amount_paid_interest:
            instrucoes.append('mensagem com juros')
        if financial_move.payment_mode_id.bank_id.bank_bic == 104:
            instrucoes.append(
                "SAC CAIXA: 0800 726 0101 (informações, reclamações, sugestões"
                " e elogios) Para pessoas com deficiência auditiva ou de fala:"
                " 0800 726 2492 o Ouvidoria: 0800 725 7474 o caixa.gov.br")
        self.boleto.instrucoes = instrucoes

    def _payment_mode(self, financial_move):
        """
        :param payment_mode:
        :return:
        """
        payment_mode_id = financial_move.payment_mode_id
        self.boleto.convenio = payment_mode_id.convenio
        self.boleto.especie_documento = \
            financial_move.document_type_id.boleto_especie
        self.boleto.aceite = payment_mode_id.boleto_aceite
        self.boleto.carteira = payment_mode_id.boleto_carteira

    def _cedente(self, partner_id):
        """
        :param company:
        :return:
        """
        self.boleto.cedente = partner_id.legal_name \
            if partner_id.legal_name else ''
        self.boleto.cedente_documento = partner_id.cnpj_cpf \
            if partner_id.cnpj_cpf else ''
        self.boleto.cedente_bairro = partner_id.district or ''
        self.boleto.cedente_cep = partner_id.zip or ''
        self.boleto.cedente_cidade = partner_id.city or ''
        self.boleto.cedente_logradouro = partner_id.street + \
            ', ' + (partner_id.number or 'SN')
        self.boleto.cedente_uf = partner_id.state_id.code or ''
        self.boleto.agencia_cedente = self.getBranchNumber()
        self.boleto.conta_cedente = self.getAccountNumber()

    def _sacado(self, partner):
        """

        :param partner:
        :return:
        """
        self.boleto.sacado_endereco = partner.street + ', ' + (
            partner.number or 'SN')
        self.boleto.sacado_cidade = partner.city
        self.boleto.sacado_bairro = partner.district
        self.boleto.sacado_uf = partner.state_id.code
        self.boleto.sacado_cep = partner.zip
        self.boleto.sacado_nome = partner.legal_name \
            if partner.legal_name else ''
        self.boleto.sacado_documento = partner.cnpj_cpf

    @classmethod
    def get_pdfs(cls, boleto_list):
        """

        :param boletoList:
        :return:
        """
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


class BoletoBB(Boleto):

    def __init__(self, financial_move, nosso_numero):
        # TODO: size o convenio and nosso numero, replace (7,2)
        # Size of convenio 4, 6, 7 or 8
        # Nosso Numero format. 1 or 2
        # Used only for convenio=6
        # 1: Nosso Numero with 5 positions
        # 2: Nosso Numero with 17 positions
        self.boleto = Boleto.getBoletoClass(financial_move)(7, 2)
        self.account_number = financial_move.payment_mode_id.bank_id.acc_number
        self.branch_number = financial_move.payment_mode_id.bank_id.bra_number
        Boleto.__init__(self, financial_move)
        self.boleto.nosso_numero = nosso_numero


class BoletoBarisul(Boleto):

    def __init__(self, financial_move, nosso_numero):
        self.boleto = Boleto.getBoletoClass(financial_move)()
        self.account_number = financial_move.payment_mode_id.bank_id.acc_number
        self.branch_number = financial_move.payment_mode_id.bank_id.bra_number
        Boleto.__init__(self, financial_move)
        self.boleto.nosso_numero = nosso_numero


class BoletoBradesco(Boleto):

    def __init__(self, financial_move, nosso_numero):
        self.boleto = Boleto.getBoletoClass(financial_move)()
        self.account_number = financial_move.payment_mode_id.bank_id.acc_number
        self.branch_number = financial_move.payment_mode_id.bank_id.bra_number
        # bank specific
        self.account_digit = \
            financial_move.payment_mode_id.bank_id.acc_number_dig
        self.branch_digit = \
            financial_move.payment_mode_id.bank_id.bra_number_dig
        # end bank specific
        Boleto.__init__(self, financial_move)
        self.boleto.nosso_numero = nosso_numero


class BoletoCaixa(Boleto):

    def __init__(self, financial_move, nosso_numero):
        self.boleto = Boleto.getBoletoClass(financial_move)()
        self.account_number = financial_move.payment_mode_id.bank_id.acc_number
        self.branch_number = financial_move.payment_mode_id.bank_id.bra_number
        # bank specific
        self.account_digit = \
            financial_move.payment_mode_id.bank_id.acc_number_dig
        # end bank specific
        Boleto.__init__(self, financial_move)
        self.boleto.nosso_numero = nosso_numero


class BoletoHsbc(Boleto):

    def __init__(self, financial_move, nosso_numero):
        self.boleto = Boleto.getBoletoClass(financial_move)()
        self.account_number = financial_move.payment_mode_id.bank_id.acc_number
        self.branch_number = financial_move.payment_mode_id.bank_id.bra_number
        Boleto.__init__(self, financial_move)
        self.boleto.nosso_numero = nosso_numero


class BoletoItau157(Boleto):

    def __init__(self, financial_move, nosso_numero):
        self.boleto = Boleto.getBoletoClass(financial_move)()
        self.account_number = financial_move.payment_mode_id.bank_id.acc_number
        self.branch_number = financial_move.payment_mode_id.bank_id.bra_number
        Boleto.__init__(self, financial_move)
        self.boleto.nosso_numero = nosso_numero


class BoletoItau(Boleto):

    def __init__(self, financial_move, nosso_numero):
        self.boleto = Boleto.getBoletoClass(financial_move)()
        self.account_number = financial_move.payment_mode_id.bank_id.acc_number
        self.branch_number = financial_move.payment_mode_id.bank_id.bra_number
        Boleto.__init__(self, financial_move)
        self.boleto.nosso_numero = nosso_numero


class BoletoReal(Boleto):

    def __init__(self, financial_move, nosso_numero):
        self.boleto = Boleto.getBoletoClass(financial_move)()
        self.account_number = financial_move.payment_mode_id.bank_id.acc_number
        self.branch_number = financial_move.payment_mode_id.bank_id.bra_number
        Boleto.__init__(self, financial_move)
        self.boleto.nosso_numero = nosso_numero


class BoletoSantander102(Boleto):

    def __init__(self, financial_move, nosso_numero):
        self.boleto = Boleto.getBoletoClass(financial_move)()
        self.account_number = financial_move.payment_mode_id.bank_id.acc_number
        self.branch_number = financial_move.payment_mode_id.bank_id.bra_number
        Boleto.__init__(self, financial_move)
        self.boleto.ios = '0'
        self.boleto.nosso_numero = nosso_numero


class BoletoStatander101201(Boleto):

    def __init__(self, financial_move, nosso_numero):
        self.boleto = Boleto.getBoletoClass(financial_move)()
        self.account_number = financial_move.payment_mode_id.bank_id.acc_number
        self.branch_number = financial_move.payment_mode_id.bank_id.bra_number
        Boleto.__init__(self, financial_move)
        self.boleto.ios = '0'
        self.boleto.nosso_numero = nosso_numero


class BoletoCaixaSigcb(Boleto):

    def __init__(self, financial_move, nosso_numero):
        from pyboleto.bank.caixa_sigcb import BoletoCaixaSigcb
        self.boleto = BoletoCaixaSigcb()
        self.account_number = financial_move.payment_mode_id.bank_id.acc_number
        self.branch_number = financial_move.payment_mode_id.bank_id.bra_number
        # bank specific
        self.account_digit = \
            financial_move.payment_mode_id.bank_id.acc_number_dig
        # end bank specific
        Boleto.__init__(self, financial_move)
        self.boleto.nosso_numero = nosso_numero


class BoletoSicredi(Boleto):

    def __init__(self, financial_move, nosso_numero):
        self.boleto = Boleto.getBoletoClass(financial_move)()
        self.account_number = financial_move.payment_mode_id.bank_id.acc_number
        self.branch_number = financial_move.payment_mode_id.bank_id.bra_number
        Boleto.__init__(self, financial_move)
        self.boleto.nosso_numero = nosso_numero
