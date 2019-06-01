# -*- coding: utf-8 -*-
# © 2012 KMEE INFORMATICA LTDA
#   @author Luis Felipe Mileo <mileo@kmee.com.br>
#   @author Daniel Sadamo <daniel.sadamo@kmee.com.br>
#   @author Fernando Marcato <fernando.marcato@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import re
import string

from ..cnab_240 import Cnab240


class Itau240(Cnab240):
    """

    """

    def __init__(self):
        """

        :return:
        """
        super(Cnab240, self).__init__()
        from cnab240.bancos import itau
        self.bank = itau

    def _prepare_header(self):
        """

        :param order:
        :return:
        """
        vals = super(Itau240, self)._prepare_header()
        # vals['cedente_dv_ag_cc'] = self.convert_int(
        #     vals['cedente_dv_ag_cc'])
        # vals['cedente_agencia_dv'] = self.convert_int(
        #     vals['cedente_agencia_dv']),
        return vals

    def _prepare_cobranca(self, line):
        """

        :param line:
        :return:
        """
        vals = super(Itau240, self)._prepare_cobranca(line)

        carteira, nosso_numero, digito = self.nosso_numero(
            line.move_line_id.transaction_ref)

        vals['cedente_dv_ag_cc'] = self.convert_int(
            vals['cedente_dv_ag_cc'])
        vals['carteira_numero'] = self.convert_int(carteira)
        vals['nosso_numero'] = self.convert_int(nosso_numero)
        vals['nosso_numero_dv'] = self.convert_int(digito)

        return vals

    # Override cnab_240.nosso_numero. Diferentes números de dígitos entre
    # CEF e Itau
    def nosso_numero(self, format):
        digito = format[-1:]
        carteira = format[:3]
        nosso_numero = re.sub(
            '[%s]' % re.escape(string.punctuation), '', format[3:-1] or '')
        return carteira, nosso_numero, digito
