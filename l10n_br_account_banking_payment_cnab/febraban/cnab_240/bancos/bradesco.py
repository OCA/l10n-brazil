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


from ..cnab_240 import Cnab240
import re
import string
from decimal import Decimal


class Bradesco240(Cnab240):

    def __init__(self):
        super(Cnab240, self).__init__()
        from cnab240.bancos import bradesco
        self.bank = bradesco

    def _prepare_header(self):
        """

        :param order:
        :return:
        """

        vals = super(Bradesco240, self)._prepare_header()
        vals['servico_servico'] = 1
        return vals

    def _prepare_segmento(self, line):
        """

        :param line:
        :return:
        """
        vals = super(Bradesco240, self)._prepare_segmento(line)
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
