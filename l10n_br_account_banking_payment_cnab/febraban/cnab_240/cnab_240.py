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

from ..cnab import Cnab
from cnab240.tipos import Arquivo
from decimal import Decimal
from openerp.addons.l10n_br_base.tools.misc import punctuation_rm
import datetime
import re
import string
import unicodedata


class Cnab240(Cnab):
    """

    """

    def __init__(self):
        super(Cnab, self).__init__()

    @staticmethod
    def get_bank(bank):
        if bank == '341':
            from bancos.itau import Itau240
            return Itau240
        elif bank == '237':
            from bancos.bradesco import Bradesco240
            return Bradesco240
        elif bank == '104':
            from bancos.cef import Cef240
            return Cef240
        elif bank == '033':
            from bancos.santander import Santander240
            return Santander240
        else:
            return Cnab240

    @property
    def inscricao_tipo(self):
        # TODO: Implementar codigo para PIS/PASEP
        if self.order.company_id.partner_id.is_company:
            return 2
        else:
            return 1

    def _prepare_header(self):
        """

        :param:
        :return:
        """
        data_de_geracao = (self.order.date_created[8:11] +
                           self.order.date_created[5:7] +
                           self.order.date_created[0:4])
        t = datetime.datetime.now() - datetime.timedelta(hours=3)  # FIXME
        hora_de_geracao = t.strftime("%H%M%S")

        return {
            'arquivo_data_de_geracao': int(data_de_geracao),
            'arquivo_hora_de_geracao': int(hora_de_geracao),
            'arquivo_sequencia': self.order.id,
            'cedente_inscricao_tipo': self.inscricao_tipo,
            'cedente_inscricao_numero': int(
                punctuation_rm(self.order.company_id.cnpj_cpf)),
            'cedente_agencia': int(self.order.mode.bank_id.bra_number),
            'cedente_conta': int(self.order.mode.bank_id.acc_number),
            'cedente_agencia_conta_dv': int(
                self.order.mode.bank_id.acc_number_dig),
            'cedente_nome': self.order.company_id.legal_name,
            'cedente_agencia_dv': int(self.order.mode.bank_id.bra_number_dig),
            'arquivo_codigo': 1,  # Remessa/Retorno
            'reservado_cedente_campo': u'REMESSA-TESTE',
            'servico_operacao': u'R',
            'codigo_transmissao': int(self.order.mode.boleto_cnab_code),
        }

    def format_date(self, srt_date):
        return int(datetime.datetime.strptime(
            srt_date, '%Y-%m-%d').strftime('%d%m%Y'))

    def nosso_numero(self, format):
        digito = format[-1:]
        carteira = format[:3]
        nosso_numero = re.sub(
            '[%s]' % re.escape(string.punctuation), '', format[3:-1] or '')
        return carteira, nosso_numero, digito

    def cep(self, format):
        sulfixo = format[-3:]
        prefixo = format[:5]
        return prefixo, sulfixo

    def sacado_inscricao_tipo(self, partner_id):
        # TODO: Implementar codigo para PIS/PASEP
        if partner_id.is_company:
            return 2
        else:
            return 1

    def rmchar(self, format):
        return re.sub('[%s]' % re.escape(string.punctuation), '', format or '')

    def _prepare_segmento(self, line):
        """

        :param line:
        :return:
        """
        carteira, nosso_numero, digito = self.nosso_numero(
            str(line.move_line_id.transaction_ref))  # TODO: Improve!
        prefixo, sulfixo = self.cep(line.partner_id.zip)

        if self.order.mode. \
                boleto_aceite == 'S':
            aceite = 'A'
        else:
            aceite = 'N'

        return {
            'cedente_agencia': int(self.order.mode.bank_id.bra_number),
            'cedente_agencia_dv': int(self.order.mode.bank_id.bra_number_dig),
            'cedente_conta': int(self.order.mode.bank_id.acc_number),
            'cedente_conta_dv': int(self.order.mode.bank_id.acc_number_dig),
            'carteira_numero': int(carteira),
            'nosso_numero': int(nosso_numero),
            'nosso_numero_dv': int(digito),
            'identificacao_titulo': u'%s' % str(line.move_line_id.move_id.id),
            'numero_documento': line.name,
            'vencimento_titulo': self.format_date(
                line.ml_maturity_date),
            'valor_titulo': Decimal("{0:,.2f}".format(
                line.move_line_id.debit)),
            'especie_titulo': int(self.order.mode.boleto_especie),
            'aceite_titulo': u'%s' % aceite,
            'data_emissao_titulo': self.format_date(
                line.ml_date_created),
            'juros_mora_taxa_dia': Decimal(
                "{0:,.2f}".format(line.move_line_id.debit * 0.00066666667)),
            # FIXME
            'valor_abatimento': Decimal('0.00'),
            'sacado_inscricao_tipo': int(
                self.sacado_inscricao_tipo(line.partner_id)),
            'sacado_inscricao_numero': int(
                self.rmchar(line.partner_id.cnpj_cpf)),
            'sacado_nome': line.partner_id.legal_name,
            'sacado_endereco': (line.partner_id.street + ',' +
                                line.partner_id.number)[:40],
            'sacado_bairro': line.partner_id.district,
            'sacado_cep': int(prefixo),
            'sacado_cep_sufixo': int(sulfixo),
            'sacado_cidade': line.partner_id.l10n_br_city_id.name,
            'sacado_uf': line.partner_id.state_id.code,
            'codigo_protesto': int(self.order.mode.boleto_protesto),
            'prazo_protesto': int(self.order.mode.boleto_protesto_prazo),
            'codigo_baixa': 0,
            'prazo_baixa': 0,
        }

    def remessa(self, order):
        """

        :param order:
        :return:
        """
        self.order = order
        self.arquivo = Arquivo(self.bank, **self._prepare_header())
        for line in order.line_ids:
            self.arquivo.incluir_cobranca(**self._prepare_segmento(line))
        remessa = unicode(self.arquivo)
        return unicodedata.normalize(
            'NFKD', remessa).encode('ascii', 'ignore')
