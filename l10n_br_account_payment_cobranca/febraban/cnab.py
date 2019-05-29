# -*- coding: utf-8 -*-
# © 2012 KMEE INFORMATICA LTDA
#   @author Luis Felipe Mileo <mileo@kmee.com.br>
#   @author Daniel Sadamo <daniel.sadamo@kmee.com.br>
#   @author Fernando Marcato <fernando.marcato@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
# TODO: implement abc factory?

from __future__ import division, print_function, unicode_literals


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
