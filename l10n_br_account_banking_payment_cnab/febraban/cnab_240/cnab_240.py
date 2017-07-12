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

from __future__ import division, print_function, unicode_literals

import datetime
import logging
import re
import string
import time
import unicodedata
from decimal import Decimal

from openerp.addons.l10n_br_base.tools.misc import punctuation_rm

from ..cnab import Cnab

_logger = logging.getLogger(__name__)
try:
    from cnab240.tipos import Arquivo
except ImportError as err:
    _logger.debug = err


class Cnab240(Cnab):
    """

    """

    def __init__(self):
        super(Cnab, self).__init__()

    @staticmethod
    def get_bank(bank):
        if bank == '341':
            from .bancos.itau import Itau240
            return Itau240
        elif bank == '237':
            from .bancos.bradesco import Bradesco240
            return Bradesco240
        elif bank == '104':
            from .bancos.cef import Cef240
            return Cef240
        elif bank == '033':
            from .bancos.santander import Santander240
            return Santander240
        elif bank == '001':
            from .bancos.bb import BB240
            return BB240
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
        return {
            'controle_banco': int(self.order.mode.bank_id.bank_bic),
            'arquivo_data_de_geracao': self.data_hoje(),
            'arquivo_hora_de_geracao': self.hora_agora(),

            # TODO: Número sequencial de arquivo
            'arquivo_sequencia': int(self.get_file_numeration()),
            'cedente_inscricao_tipo': self.inscricao_tipo,
            'cedente_inscricao_numero': int(punctuation_rm(
                self.order.company_id.cnpj_cpf)),
            'cedente_agencia': int(
                self.order.mode.bank_id.bra_number),
            'cedente_conta': int(self.order.mode.bank_id.acc_number),
            'cedente_conta_dv': (self.order.mode.bank_id.acc_number_dig),
            'cedente_agencia_dv': self.order.mode.bank_id.bra_number_dig,
            'cedente_nome': self.order.company_id.legal_name,
            # DV ag e conta
            'cedente_dv_ag_cc': (self.order.mode.bank_id.bra_acc_dig),

            # 'arquivo_codigo': 1,  # Remessa/Retorno
            'servico_operacao': u'R',
            'nome_banco': unicode(self.order.mode.bank_id.bank_name),
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
        return re.sub('[%s]' % re.escape(string.punctuation), '',
                      format or '')

    def _prepare_cobranca(self, line):
        """
        :param line:
        :return:
        """
        prefixo, sulfixo = self.cep(line.partner_id.zip)

        aceite = u'N'
        if not self.order.mode.boleto_aceite == 'S':
            aceite = u'A'

        # Código agencia do cedente
        # cedente_agencia = cedente_agencia

        # Dígito verificador da agência do cedente
        # cedente_agencia_conta_dv = cedente_agencia_dv

        # Código da conta corrente do cedente
        # cedente_conta = cedente_conta

        # Dígito verificador da conta corrente do cedente
        # cedente_conta_dv = cedente_conta_dv

        # Dígito verificador de agencia e conta
        # Era cedente_agencia_conta_dv agora é cedente_dv_ag_cc

        return {
            'controle_banco': int(self.order.mode.bank_id.bank_bic),
            'cedente_agencia': int(self.order.mode.bank_id.bra_number),
            'cedente_conta': int(self.order.mode.bank_id.acc_number),
            'cedente_conta_dv': self.order.mode.bank_id.acc_number_dig,
            'cedente_agencia_dv': self.order.mode.bank_id.bra_number_dig,
            # DV ag e cc
            'cedente_dv_ag_cc': (self.order.mode.bank_id.bra_acc_dig),
            'identificacao_titulo': u'0000000',  # TODO
            'identificacao_titulo_banco': u'0000000',  # TODO
            'identificacao_titulo_empresa': line.move_line_id.move_id.name,
            'numero_documento': line.name,
            'vencimento_titulo': self.format_date(
                line.ml_maturity_date),
            'valor_titulo': Decimal(str(line.amount_currency)).quantize(
                Decimal('1.00')),
            # TODO: fépefwfwe
            # TODO: Código adotado para identificar o título de cobrança.
            # 8 é Nota de cŕedito comercial
            'especie_titulo': int(self.order.mode.boleto_especie),
            'aceite_titulo': aceite,
            'data_emissao_titulo': self.format_date(
                line.ml_date_created),
            # TODO: trazer taxa de juros do Odoo. Depende do valor do 27.3P
            # CEF/FEBRABAN e Itaú não tem.
            'juros_mora_data': self.format_date(
                line.ml_maturity_date),
            'juros_mora_taxa_dia': Decimal('0.00'),
            'valor_abatimento': Decimal('0.00'),
            'sacado_inscricao_tipo': int(
                self.sacado_inscricao_tipo(line.partner_id)),
            'sacado_inscricao_numero': int(
                self.rmchar(line.partner_id.cnpj_cpf)),
            'sacado_nome': line.partner_id.legal_name,
            'sacado_endereco': (
                line.partner_id.street + ' ' + line.partner_id.number),
            'sacado_bairro': line.partner_id.district,
            'sacado_cep': int(prefixo),
            'sacado_cep_sufixo': int(sulfixo),
            'sacado_cidade': line.partner_id.l10n_br_city_id.name,
            'sacado_uf': line.partner_id.state_id.code,
            'codigo_protesto': int(self.order.mode.boleto_protesto),
            'prazo_protesto': int(self.order.mode.boleto_protesto_prazo),
            'codigo_baixa': 2,
            'prazo_baixa': 0,  # De 5 a 120 dias.
            'controlecob_data_gravacao': self.data_hoje(),
            'cobranca_carteira': int(self.order.mode.boleto_carteira),
        }

    def _prepare_pagamento(self, line):
        vals = {
            # CONTROLE
            # 01.3A
            'controle_banco': int(self.order.mode.bank_id.bank_bic),
            # 02.3A
            'controle_lote': 1,
            # 03.3A -  3-Registros Iniciais do Lote
            'controle_registro': 3,

            # SERVICO
            # 04.3A - Nº Seqüencial do Registro - Inicia em 1 em cada novo lote
            # TODO: Contador para o sequencial do lote
              'servico_numero_registro': 1,
            # 05.3A
            #   Segmento Código de Segmento do Reg.Detalhe
            # 06.3A
            'servico_tipo_movimento': self.order.tipo_movimento or 1,
            # 07.3A
            'servico_codigo_movimento': self.order.tipo_movimento or 00,

            # FAVORECIDO
            # 08.3A - 018-TED 700-DOC
            'favorecido_camara': 0,
            # 09.3A
            'favorecido_banco': int(line.bank_id.bank_bic),
            # 10.3A
            'favorecido_agencia': int(line.bank_id.bra_number),
            # 11.3A
            'favorecido_agencia_dv': line.bank_id.bra_number_dig,
            # 12.3A
            'favorecido_conta': int(line.bank_id.acc_number),
            # 13.3A
            'favorecido_dv': line.bank_id.acc_number_dig[0],
            # 14.3A
            'favorecido_conta_dv': line.bank_id.acc_number_dig[1]
                if len(line.bank_id.bra_number_dig) > 1 else '',
            # 15.3A
            'favorecido_nome': line.partner_id.name,

            # CREDITO
            # 16.3A -
            'credito_seu_numero': line.name,
            # 17.3A
            'credito_data_pagamento': self.format_date(line.date),
            # 18.3A
            'credito_moeda_tipo': line.currency.name,
            # 19.3A
            'credito_moeda_quantidade': Decimal('0.00000'),
            # 20.3A
            'credito_valor_pagamento':
                Decimal(str(line.amount_currency)).quantize(Decimal('1.00')),
            # 21.3A
            # 'credito_nosso_numero': '',
            # 22.3A
            # 'credito_data_real': '',
            # 23.3A
            # 'credito_valor_real': '',

            # INFORMAÇÔES
            # 24.3A
            # 'outras_informacoes': '',
            # 25.3A
            # 'codigo_finalidade_doc': line.codigo_finalidade_doc,
            # 26.3A
            'codigo_finalidade_ted': line.codigo_finalidade_ted or '',
            # 27.3A
            'codigo_finalidade_complementar':
                line.codigo_finalidade_complementar or '',
            # 28.3A
            # CNAB - Uso Exclusivo FEBRABAN/CNAB
            # 29.3A
            # 'aviso_ao_favorecido': line.aviso_ao_favorecido,
            'aviso_ao_favorecido': 0,
            # 'ocorrencias': '',

            # REGISTRO B
            # 01.3B
            # 02.3B
            # 03.3B
            # 04.3B
            # 05.3B
            # 06.3B

            # DADOS COMPLEMENTARES - FAVORECIDOS
            # 07.3B
            'favorecido_tipo_inscricao': self.inscricao_tipo(line.partner_id),
            # 08.3B
            'favorecido_num_inscricao':
                int(punctuation_rm(line.partner_id.cnpj_cpf)),
            # 09.3B
            'favorecido_endereco_rua': line.partner_id.street or '',
            # 10.3B
            'favorecido_endereco_num': int(line.partner_id.number) or 0,
            # 11.3B
            'favorecido_endereco_complemento': line.partner_id.street2 or '',
            # 12.3B
            'favorecido_endereco_bairro': line.partner_id.district or '',
            # 13.3B
            'favorecido_endereco_cidade':
                line.partner_id.l10n_br_city_id.name or '',
            # 14.3B
            'favorecido_cep': int(line.partner_id.zip[:5]) or 0,
            # 15.3B
            'favorecido_cep_complemento': line.partner_id.zip[6:9] or '',
            # 16.3B
            'favorecido_estado': line.partner_id.state_id.code or '',

            # DADOS COMPLEMENTARES - PAGAMENTO
            # 17.3B
            'pagamento_vencimento': 0,
            # 18.3B
            'pagamento_valor_documento': Decimal('0.00'),
            # 19.3B
            'pagamento_abatimento': Decimal('0.00'),
            # 20.3B
            'pagamento_desconto': Decimal('0.00'),
            # 21.3B
            'pagamento_mora': Decimal('0.00'),
            # 22.3B
            'pagamento_multa': Decimal('0.00'),
            # 23.3B
            # TODO: Verificar se este campo é retornado no retorno
            # 'cod_documento_favorecido': '',
            # 24.3B - Informado No SegmentoA
            # 'aviso_ao_favorecido': '0',
            # 25.3B
            # 'codigo_ug_centralizadora': '0',
            # 26.3B
            # 'codigo_ispb': '0',
        }
        return vals

    def remessa(self, order):
        """

        :param order:
        :return:
        """
        cobrancasimples_valor_titulos = 0

        self.order = order
        self.arquivo = Arquivo(self.bank, **self._prepare_header())

        if order.payment_order_type == 'payment':
            incluir = self.arquivo.incluir_debito_pagamento
            prepare = self._prepare_pagamento
        else:
            incluir = self.arquivo.incluir_cobranca
            prepare = self._prepare_cobranca

        for line in order.line_ids:
            incluir(**prepare(line))
            self.arquivo.lotes[0].header.servico_servico = 1
            # TODO: tratar soma de tipos de cobranca
            # cobrancasimples_valor_titulos += line.amount_currency
            # self.arquivo.lotes[0].trailer.cobrancasimples_valor_titulos = \
            #     Decimal(cobrancasimples_valor_titulos).quantize(
            #         Decimal('1.00'))

        remessa = unicode(self.arquivo)
        return unicodedata.normalize(
            'NFKD', remessa).encode('ascii', 'ignore')

    def data_hoje(self):
        return (int(time.strftime("%d%m%Y")))

    def hora_agora(self):
        return (int(time.strftime("%H%M%S")))
