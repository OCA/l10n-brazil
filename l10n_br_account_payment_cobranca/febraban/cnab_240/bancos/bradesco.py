# -*- coding: utf-8 -*-
# © 2012 KMEE INFORMATICA LTDA
#   @author Luis Felipe Mileo <mileo@kmee.com.br>
#   @author Daniel Sadamo <daniel.sadamo@kmee.com.br>
#   @author Fernando Marcato <fernando.marcato@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import re
import string
from decimal import Decimal

from ..cnab_240 import Cnab240


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

    def _prepare_cobranca(self, line):
        """

        :param line:
        :return:
        """
        vals = super(Bradesco240, self)._prepare_cobranca(line)
        vals['prazo_baixa'] = unicode(str(
            vals['prazo_baixa']), "utf-8")
        vals['desconto1_percentual'] = Decimal('0.00')
        vals['valor_iof'] = Decimal('0.00')
        # vals['cobrancasimples_valor_titulos'] = Decimal('02.00')
        vals['identificacao_titulo_banco'] = self.convert_int(
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
