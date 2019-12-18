# -*- coding: utf-8 -*-
# © 2012 KMEE INFORMATICA LTDA
#   @author Luis Felipe Mileo <mileo@kmee.com.br>
#   @author Daniel Sadamo <daniel.sadamo@kmee.com.br>
#   @author Fernando Marcato <fernando.marcato@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from ..cnab_240 import Cnab240


class Santander240(Cnab240):
    """

    """

    def __init__(self):
        """

        :return:
        """
        super(Cnab240, self).__init__()
        from cnab240.bancos import santander
        self.bank = santander

    def _prepare_header(self):
        """

        :param order:
        :return:
        """
        vals = super(Santander240, self)._prepare_header()
        del vals['arquivo_hora_de_geracao']
        return vals

    def _prepare_cobranca(self, line):
        """

        :param line:
        :return:
        """
        vals = super(Santander240, self)._prepare_cobranca(line)
        return vals
