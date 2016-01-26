# coding: utf-8
# ###########################################################################
#
#    Author: Luis Felipe Mileo
#            Fernando Marcato Rodrigues
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


from ..pag_for500 import PagFor500
import re
import string


class BradescoPagFor(PagFor500):
    def __init__(self):
        super(PagFor500, self).__init__()
        from cnab240.bancos import bradescoPagFor
        self.bank = bradescoPagFor
        self.controle_linha = 2

    def _prepare_header(self):
        """

        :param order:
        :return:
        """
        vals = super(BradescoPagFor, self)._prepare_header()
        vals['codigo_comunicacao'] = int(self.order.mode.boleto_convenio)
        return vals

    def _prepare_segmento(self, line, vals):
        """

        :param line:
        :return:
        """
        vals = super(BradescoPagFor, self)._prepare_segmento(line, vals)

        # TODO campo para informar a data do pagamento.
        vals['data_para_efetivacao_pag'] = self.muda_campos_data(
            vals['vencimento_titulo'])
        self.controle_linha += 1

        return vals

    # Override cnab_240.nosso_numero. Diferentes números de dígitos
    #  entre CEF e Itau
    def nosso_numero(self, format):
        digito = format[-1:]
        carteira = format[:3]
        nosso_numero = re.sub(
            '[%s]' % re.escape(string.punctuation), '', format[3:-1] or '')
        return carteira, nosso_numero, digito

    def muda_campos_data(self, campo):
        campo = str(campo)
        campo = campo[-4:] + campo[2:4] + campo[:2]
        return int(campo)
