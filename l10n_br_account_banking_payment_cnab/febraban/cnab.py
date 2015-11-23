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
# TODO: implement abc factory?


class Cnab(object):
    def __init__(self):
        pass

    @staticmethod
    def get_cnab(bank, cnab_type='240'):
        if cnab_type == '240':
            from .cnab_240.cnab_240 import Cnab240
            return Cnab240.get_bank(bank)
        elif cnab_type == '400':
            from .cnab_400.cnab_400 import Cnab400
            return Cnab400.get_bank(bank)
        elif cnab_type == '500':
            from .pag_for.pag_for500 import PagFor500
            return PagFor500.get_bank(bank)
        else:
            return False

    def remessa(self, order):
        return False

    def retorno(self, cnab_file):
        return object
