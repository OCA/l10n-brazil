# -*- coding: utf-8 -*-
# © 2012 KMEE INFORMATICA LTDA
#   @author Luis Felipe Mileo <mileo@kmee.com.br>
#   @author Daniel Sadamo <daniel.sadamo@kmee.com.br>
#   @author Fernando Marcato <fernando.marcato@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from __future__ import division, print_function, unicode_literals

import logging
import base64
import codecs

_logger = logging.getLogger(__name__)


try:
    from cnab240.tipos import ArquivoCobranca400
except ImportError as err:
    _logger.debug = (err)


class Cnab(object):

    def __init__(self):
        self.arquivo = False
        self.cnab_type = False

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

    @staticmethod
    def gerar_remessa(order):
        cnab = Cnab.get_cnab(
            order.company_partner_bank_id.bank_id.code_bc,
            order.payment_mode_id.payment_method_id.code
        )()
        return cnab.remessa(order)

    @staticmethod
    def detectar_retorno(cnab_file_object):
        arquivo_retono = base64.b64decode(cnab_file_object)
        f = open('/tmp/cnab_retorno.ret', 'wb')
        f.write(arquivo_retono)
        f.close()
        arquivo_retorno = codecs.open(
            '/tmp/cnab_retorno.ret',
            encoding='ascii'
        )
        header = arquivo_retorno.readline()
        arquivo_retorno.seek(0)

        if 210 < len(header) < 410:
            cnab_type = '400'
            banco = header[76:79]
        elif len(header) < 210:
            cnab_type = '240'
            banco = header[:3]

        cnab = Cnab.get_cnab(banco, cnab_type)()
        return cnab_type, cnab.retorno(arquivo_retorno)

    def retorno(self, arquivo_retorno):
        return ArquivoCobranca400(
            self.classe_retorno,
            arquivo=arquivo_retorno
        )

    def remessa(self, order):
        pass

    def convert_int(self, campo):
        if campo:
            return int(campo)
        # Retornamos de propósito vazio para que a cnab240 acuse o erro do
        # registro em branco pois, se retornarmos ZERO o erro vai passar
        # despercebido
        return ''
