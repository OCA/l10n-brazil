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

from ..cnab import Cnab
from cnab240.tipos import Arquivo
from decimal import Decimal
from openerp.addons.l10n_br_base.tools.misc import punctuation_rm
import datetime
import re
import string
import unicodedata
import time


class PagFor500(Cnab):
    """

    """

    def __init__(self):
        super(Cnab, self).__init__()

    @staticmethod
    def get_bank(bank):
        if bank == '237':
            from .bancos.bradesco import BradescoPagFor
            return BradescoPagFor
        else:
            return PagFor500

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
        return {
            'arquivo_data_de_geracao': self.data_hoje(),
            'arquivo_hora_de_geracao': self.hora_agora(),
            # TODO: Número sequencial de arquivo
            'numero_remessa': int(self.get_file_numeration()),
            'cedente_inscricao_tipo': self.inscricao_tipo,
            'cnpj_cpf_base': int(punctuation_rm(
                self.order.company_id.cnpj_cpf)[0:8]),
            'cnpj_cpf_filial': int(punctuation_rm(
                self.order.company_id.cnpj_cpf)[9:12]),
            'controle_cnpj': int(punctuation_rm(
                self.order.company_id.cnpj_cpf)[12:14]),
            'cedente_agencia': int(self.order.mode.bank_id.bra_number),
            'cedente_conta': int(self.order.mode.bank_id.acc_number),
            'cedente_agencia_conta_dv':
            self.order.mode.bank_id.bra_number_dig,
            'nome_empresa_pagadora': self.order.company_id.legal_name,
            'cedente_codigo_agencia_digito':
            self.order.mode.bank_id.bra_number_dig,
            'arquivo_codigo': 1,  # Remessa/Retorno
            'servico_operacao': u'R',
            'reservado_empresa': u'BRADESCO PAG FOR',
            # Sequencial crescente e nunca pode ser repetido
            'numero_lista_debito': int(self.get_file_numeration()),
            # TODO: Sequencial crescente de 1 a 1 no arquivo. O primeiro header
            #  será sempre 000001
            'sequencial': 1
        }

    def get_file_numeration(self):
        numero = self.order.get_next_number()
        if not numero:
            numero = 1
        return numero

    def format_date(self, srt_date):
        return int(datetime.datetime.strptime(
            srt_date, '%Y-%m-%d').strftime('%d%m%Y'))

    def nosso_numero(self, format):
        pass

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

        prefixo, sulfixo = self.cep(line.partner_id.zip)

        aceite = u'N'
        if not self.order.mode.boleto_aceite == 'S':
            aceite = u'A'

        return {
            'especie_titulo': 8,
            # TODO: Código adotado para identificar o título de cobrança. 8
            # é Nota de cŕedito comercial
            'aceite_titulo': aceite,
            'tipo_inscricao': int(
                self.sacado_inscricao_tipo(line.partner_id)),
            'cnpj_cpf_base_forn': int(
                self.rmchar(line.partner_id.cnpj_cpf)[0:8]),
            'cnpj_cpf_filial_forn': int(
                self.rmchar(line.partner_id.cnpj_cpf)[9:12]),
            'controle_cnpj_cpf_forn': int(
                self.rmchar(line.partner_id.cnpj_cpf)[12:14]),
            'nome_forn': line.partner_id.legal_name,
            'endereco_forn': (
                line.partner_id.street + ' ' + line.partner_id.number),
            'cep_complemento_forn': int(sulfixo),
            # TODO: código do banco. Para a Modalidade de Pagamento valor
            # pode variar
            'codigo_banco_forn': 237,
            'codigo_agencia_forn': int(self.order.mode.bank_id.bra_number),
            'digito_agencia_forn': self.order.mode.bank_id.bra_number_dig,
            'conta_corrente_forn': int(self.order.mode.bank_id.acc_number),
            'digito_conta_forn': self.order.mode.bank_id.acc_number_dig,
            # TODO Gerado pelo cliente pagador quando do agendamento de
            # pagamento por parte desse, exceto para a modalidade 30 -
            # Títulos em Cobrança Bradesco
            'numero_pagamento': int(line.move_line_id.move_id.name),
            'carteira': int(self.order.mode.boleto_carteira),
            'nosso_numero': 11,
            'numero_documento': line.name,
            'vencimento_titulo': self.format_date(
                line.ml_maturity_date),
            'data_emissao_titulo': self.format_date(
                line.ml_date_created),
            'desconto1_data': 0,
            'fator_vencimento': 0,  # FIXME
            'valor_titulo': Decimal(str(line.amount_currency)).quantize(
                Decimal('1.00')),
            'valor_pagto': Decimal(str(line.amount_currency)).quantize(
                Decimal('1.00')),
            'valor_desconto': Decimal('0.00'),
            'valor_acrescimo': Decimal('0.00'),
            'tipo_documento': 2,
            # NF_Fatura_01/Fatura_02/NF_03/Duplicata_04/Outros_05
            'numero_nf': int(line.ml_inv_ref.internal_number),
            # 'serie_documento': u'AB',
            'modalidade_pagamento': int(self.order.mode.boleto_especie),
            'tipo_movimento': 0,
            # TODO Tipo de Movimento.
            # 0 - Inclusão.
            # 5 - Alteração.
            # 9 - Exclusão. Wkf Odoo.
            'codigo_movimento': 0,  # FIXME
            # 'horario_consulta_saldo': u'5',  # FIXME
            'codigo_area_empresa': 0,
            'codigo_lancamento': 0,  # FIXME
            'tipo_conta_fornecedor': 1,  # FIXME
            # O Primeiro registro de transação sempre será o registro
            # “000002”, e assim sucessivamente.
            'sequencial': 3,  # FIXME

            # Trailer
            'totais_quantidade_registros': 0,
            'total_valor_arq': Decimal('0.00'),
            # FIXME: lib nao reconhece campo
            'sequencial_trailer': int(self.get_file_numeration()),
            'sequencial_transacao': self.controle_linha,
            'codigo_protesto': int(self.order.mode.boleto_protesto),
            'prazo_protesto': int(self.order.mode.boleto_protesto_prazo),
            'codigo_baixa': 2,
            'prazo_baixa': 0,  # De 5 a 120 dias.
            'controlecob_data_gravacao': self.data_hoje(),

        }

    def remessa(self, order):
        """

        :param order:
        :return:
        """

        pag_valor_titulos = 0

        self.order = order
        self.arquivo = Arquivo(self.bank, **self._prepare_header())
        cont_lote = 0

        for line in order.line_ids:
            self.arquivo.incluir_pagamento(**self._prepare_segmento(line))
            pag_valor_titulos += line.amount_currency
            self.arquivo.trailer.total_valor_arq = Decimal(
                pag_valor_titulos).quantize(Decimal('1.00'))
            self.arquivo.trailer.sequencial_transacao = self.controle_linha

            cont_lote += 1
        remessa = unicode(self.arquivo)
        return unicodedata.normalize(
            'NFKD', remessa).encode('ascii', 'ignore')

    def data_hoje(self):
        return (int(time.strftime("%d%m%Y")))

    def hora_agora(self):
        return (int(time.strftime("%H%M%S")))
