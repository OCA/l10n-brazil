# coding: utf-8
# ###########################################################################
#
#    Author: Luis Felipe Mileo
#            Fernando Marcato Rodrigues
#            Daniel Sadamo Hirayama
#    Copyright 2015 KMEE - www.kmee.com.br
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


from ..cnab_400 import Cnab400
import re
import string
from decimal import Decimal


class Bradesco400(Cnab400):

    def __init__(self):
        super(Cnab400, self).__init__()
        from cnab240.bancos import bradesco_cobranca_400
        self.bank = bradesco_cobranca_400
        self.controle_linha = 2

    def _prepare_header(self):
        """

        :param order:
        :return:
        """

        vals = super(Bradesco400, self)._prepare_header()
        vals['servico_servico'] = 1
        return vals

    def _prepare_segmento(self, line):
        """

        :param line:
        :return:
        """
        vals = super(Bradesco400, self)._prepare_segmento(line)
        vals['prazo_baixa'] = unicode(str(
            vals['prazo_baixa']), "utf-8")
        vals['desconto1_percentual'] = Decimal('0.00')
        vals['valor_iof'] = Decimal('0.00')
        # vals['cobrancasimples_valor_titulos'] = Decimal('02.00')
        vals['identificacao_titulo_banco'] = int(
            vals['identificacao_titulo_banco'])
        vals['cedente_conta_dv'] = unicode(str(
            vals['cedente_conta_dv']), "utf-8")
        vals['cedente_agencia_dv'] = unicode(str(
            vals['cedente_agencia_dv']), "utf-8")
        vals['cedente_dv_ag_cc'] = unicode(str(
            vals['cedente_dv_ag_cc']), "utf-8")

        vals['sacado_cc_dv'] = u'0'
        vals['identificacao_empresa_beneficiaria_banco'] = \
            self.retorna_id_empr_benef()
        vals['digito_conferencia_numero_bancario'] = u'0'
        vals['condicao_emissao_papeleta'] = 1

        vals['indicador_rateio_credito'] = u""
        self.controle_linha += 1

        return vals

    def nosso_numero(self, format):
        digito = format[-1:]
        carteira = format[:3]
        nosso_numero = re.sub(
            '[%s]' % re.escape(string.punctuation), '', format[3:-1] or '')
        return carteira, nosso_numero, digito

    def retorna_id_empr_benef(self):
        dig_cart = 3
        dig_ag = 5
        dig_conta = 7

        carteira = self.adiciona_digitos(
            self.order.mode.boleto_carteira, dig_cart)
        agencia = self.adiciona_digitos(
            self.order.mode.bank_id.bra_number, dig_ag)
        conta = self.adiciona_digitos(
            self.order.mode.bank_id.acc_number, dig_conta)

        ident = u'0' + (carteira) + (agencia) + (conta) + \
                (self.order.mode.bank_id.acc_number_dig)
        return ident

    def adiciona_digitos(self, campo, num_digitos):
        chars_faltantes = num_digitos - len(campo)
        return (u'0' * chars_faltantes) + campo


def str_to_unicode(inp_str):
    inp_str = unicode(inp_str, "utf-8")
    return inp_str
