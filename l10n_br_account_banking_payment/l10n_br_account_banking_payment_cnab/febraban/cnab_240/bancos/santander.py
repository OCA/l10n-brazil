# coding: utf-8
# ###########################################################################
#
#    Author: Luis Felipe Mileo
#            Fernando Marcato Rodrigues
#            Daniel Sadamo Hirayama
#            Gustavo Lepri
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

    def _prepare_segmento(self, line):
        """

        :param line:
        :return:
        """
        vals = super(Santander240, self)._prepare_segmento(line)
        return vals
