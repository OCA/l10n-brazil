# -*- coding: utf-8 -*-
# © 2012 KMEE INFORMATICA LTDA
#   @author Luis Felipe Mileo <mileo@kmee.com.br>
#   @author Fernando Marcato <fernando.marcato@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


import re
import string

from ..pag_for500 import PagFor500


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
        vals['codigo_comunicacao'] = self.convert_int(
            self.order.payment_mode_id.boleto_convenio)
        return vals

    def _prepare_cobranca(self, line, vals):
        """

        :param line:
        :return:
        """
        vals = super(BradescoPagFor, self)._prepare_cobranca(line, vals)

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
        return self.convert_int(campo)
