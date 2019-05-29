# coding: utf-8

from __future__ import division, print_function, unicode_literals

import re
import string

from ..cnab_240 import Cnab240


class BB240(Cnab240):

    def __init__(self):
        super(Cnab240, self).__init__()
        from cnab240.bancos import bancodobrasil
        self.bank = bancodobrasil

    def _prepare_header(self):
        """
        Preparar header do arquivo.
        Adicionar informações no header do arquivo do Banco do Brasil
        """
        vals = super(BB240, self)._prepare_header()
        # vals['servico_servico'] = 1
        return vals

    def _prepare_cobranca(self, line):
        """
        Preparar o evento (segmentoA e segmentoB) apartir da payment.line
        :param line - payment.line
        :return: dict - Informações
        """
        vals = super(BB240, self)._prepare_cobranca(line)
        # vals['prazo_baixa'] = unicode(str(
        #     vals['prazo_baixa']), "utf-8")
        # vals['desconto1_percentual'] = Decimal('0.00')
        # vals['valor_iof'] = Decimal('0.00')
        # # vals['cobrancasimples_valor_titulos'] = Decimal('02.00')
        # vals['identificacao_titulo_banco'] = int(
        #     vals['identificacao_titulo_banco'])
        # vals['cedente_conta_dv'] = unicode(str(
        #     vals['cedente_conta_dv']), "utf-8")
        # vals['cedente_agencia_dv'] = unicode(str(
        #     vals['cedente_agencia_dv']), "utf-8")
        # vals['cedente_dv_ag_cc'] = unicode(str(
        #     vals['cedente_dv_ag_cc']), "utf-8")
        return vals

    # Override cnab_240.nosso_numero. Diferentes números de dígitos entre
    # CEF e Itau
    def nosso_numero(self, format):
        digito = format[-1:]
        carteira = format[:3]
        nosso_numero = re.sub(
            '[%s]' % re.escape(string.punctuation), '', format[3:-1] or '')
        return carteira, nosso_numero, digito

    def str_to_unicode(inp_str):
        inp_str = unicode(inp_str, "utf-8")
        return inp_str
