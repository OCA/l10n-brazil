# -*- coding: utf-8 -*-
# © 2012 KMEE INFORMATICA LTDA
#   @author Luis Felipe Mileo <mileo@kmee.com.br>
#   @author Daniel Sadamo <daniel.sadamo@kmee.com.br>
#   @author Fernando Marcato <fernando.marcato@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from __future__ import division, print_function, unicode_literals

import datetime
import logging
import re
import string
import time
import unicodedata
from decimal import Decimal

from odoo.addons.l10n_br_base.tools.misc import punctuation_rm

from ..cnab import Cnab

_logger = logging.getLogger(__name__)
try:
    from cnab240.tipos import Arquivo, Lote
except ImportError as err:
    _logger.debug = err


class Cnab240(Cnab):
    """
    CNAB240
    """

    def __init__(self):
        super(Cnab, self).__init__()

    @staticmethod
    def get_bank(bank):
        '''
        Função chamada na criação do CNAB que dado o código do banco,
        instancia o objeto do banco e retorna o obj ao CNAB que sera criado.
        :param bank: str - Código do banco
        :return:
        '''
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

    def get_inscricao_tipo(self, partner_id):
        # TODO: Implementar codigo para PIS/PASEP
        if partner_id.is_company:
            return 2
        else:
            return 1

    def _prepare_header(self):
        """
        Preparar o header do arquivo do CNAB
        :return: dict - Header do arquivo
        """
        header_arquivo = {
            # CONTROLE
            # 01.0
            'controle_banco': int(
                self.order.company_partner_bank_id.bank_id.code_bc
            ),
            # 02.0 # Sequencia para o Arquivo
            'controle_lote': 1,
            # 03.0  0- Header do Arquivo
            'controle_registro': 0,
            # 04.0
            # CNAB - Uso Exclusivo FEBRABAN / CNAB

            # EMPRESA
            # 05.0 - 1 - CPF / 2 - CNPJ
            'cedente_inscricao_tipo':
                self.get_inscricao_tipo(self.order.company_id.partner_id),
            # 06.0
            'cedente_inscricao_numero':
                int(punctuation_rm(self.order.company_id.cnpj_cpf)),
            # 07.0
            'cedente_convenio': '0001222130126',
            # 08.0
            'cedente_agencia':
                int(self.order.company_partner_bank_id.bra_number),
            # 09.0
            'cedente_agencia_dv':
                self.order.company_partner_bank_id.bra_number_dig,
            # 10.0
            'cedente_conta':
                int(punctuation_rm(
                    self.order.company_partner_bank_id.acc_number)),
            # 11.0
            'cedente_conta_dv':
                self.order.company_partner_bank_id.acc_number_dig[0],
            # 12.0
            'cedente_agencia_conta_dv':
                self.order.company_partner_bank_id.acc_number_dig[1]
                if len(
                    self.order.company_partner_bank_id.acc_number_dig
                ) > 1 else '',
            # 13.0
            'cedente_nome':
                self.order.company_partner_bank_id.partner_id.legal_name[:30]
                if self.order.company_partner_bank_id.partner_id.legal_name
                else self.order.company_partner_bank_id.partner_id.name[:30],
            # 14.0
            'nome_banco': self.order.company_partner_bank_id.bank_name,
            # 15.0
            #   CNAB - Uso Exclusivo FEBRABAN / CNAB

            # ARQUIVO
            # 16.0 Código Remessa = 1 / Retorno = 2
            'arquivo_codigo': '1',
            # 17.0
            'arquivo_data_de_geracao': self.data_hoje(),
            # 18.0
            'arquivo_hora_de_geracao': self.hora_agora(),
            # 19.0 TODO: Número sequencial de arquivo
            'arquivo_sequencia': int(self.get_file_numeration()),
            # 20.0
            'arquivo_layout': 103,
            # 21.0
            'arquivo_densidade': 0,
            # 22.0
            'reservado_banco': '',
            # 23.0
            'reservado_empresa': 'EMPRESA 100',
            # 24.0
            # CNAB - Uso Exclusivo FEBRABAN / CNAB
        }

        return header_arquivo

    def _prepare_header_lote(self):
        """
        Preparar o header de LOTE para arquivo do CNAB
        :return: dict - Header do arquivo
        """
        empresa = self.order.company_partner_bank_id.partner_id

        header_arquivo_lote = {

            # CONTROLE
            # 01.1
            'controle_banco': int(self.order.company_partner_bank_id.code_bc),
            # 02.1  Sequencia para o Arquivo
            'controle_lote': 1,
            # 03.1  0- Header do Arquivo
            'controle_registro': 1,

            # SERVICO
            # 04.1 # Header do lote sempre 'C'
            'servico_operacao': 'C',
            # 05.1
            'servico_servico': self.order.tipo_servico,
            # 06.1
            'servico_forma_lancamento': 1,
            # 07.1
            'servico_layout': 20,
            # 08.1
            # CNAB - Uso Exclusivo da FEBRABAN/CNAB

            # EMPRESA CEDENTE
            # 09.1
            'empresa_inscricao_tipo': 2,
            # self.get_inscricao_tipo(self.order.company_id.partner_id),
            # 10.1
            'empresa_inscricao_numero': punctuation_rm(empresa.cnpj_cpf),
            # 11.1
            'cedente_convenio': self.order.codigo_convenio,
            # 12.1
            'cedente_agencia':
                int(self.order.company_partner_bank_id.bra_number),
            # 13.1
            'cedente_agencia_dv':
                self.order.company_partner_bank_id.bra_number_dig,
            # 14.1
            'cedente_conta':
                int(punctuation_rm(
                    self.order.company_partner_bank_id.acc_number)),
            # 15.1
            'cedente_conta_dv':
                self.order.company_partner_bank_id.acc_number_dig[0],
            # 16.1
            'cedente_agencia_conta_dv':
                self.order.company_partner_bank_id.acc_number_dig[1]
                if len(
                    self.order.company_partner_bank_id.acc_number_dig
                ) > 1 else '',
            # 17.1
            'cedente_nome':
                self.order.company_partner_bank_id.partner_id.legal_name[:30]
                if self.order.company_partner_bank_id.partner_id.legal_name
                else self.order.company_partner_bank_id.partner_id.name[:30],
            # 18.1
            'mensagem1': '',

            # ENDERECO
            # 19.1
            'empresa_logradouro': empresa.street,
            # 20.1
            'empresa_endereco_numero': empresa.number,
            # 21.1
            'empresa_endereco_complemento': empresa.street2,
            # 22.1
            'empresa_endereco_cidade': empresa.l10n_br_city_id.name,
            # 23.1
            'empresa_endereco_cep': self.get_cep('prefixo', empresa.zip),
            # 24.1
            'empresa_endereco_cep_complemento':
                self.get_cep('sufixo', empresa.zip),
            # 25.1
            'empresa_endereco_estado': empresa.state_id.code,

            # 26.1
            'indicativo_forma_pagamento': '',
            # 27.1
            # CNAB - Uso Exclusivo FEBRABAN / CNAB
            # 28.1
            'ocorrencias': '',
        }
        return header_arquivo_lote

    def get_file_numeration(self):
        # Função para retornar a numeração sequencial do arquivo
        return 1

    def _prepare_cobranca(self, line):
        """
        :param line:
        :return:
        """
        # prefixo, sufixo = self.cep(line.partner_id.zip)

        aceite = u'N'
        if not self.order.payment_mode_id.boleto_aceite == 'S':
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
            'controle_banco': int(
                self.order.company_partner_bank_id.code_bc),
            'cedente_agencia': int(
                self.order.company_partner_bank_id.bra_number),
            'cedente_conta': int(
                self.order.company_partner_bank_id.acc_number),
            'cedente_conta_dv':
                self.order.company_partner_bank_id.acc_number_dig,
            'cedente_agencia_dv':
                self.order.company_partner_bank_id.bra_number_dig,
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
            'especie_titulo': int(self.order.payment_mode_id.boleto_especie),
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
                self.get_inscricao_tipo(line.partner_id)),
            'sacado_inscricao_numero': line.partner_id.cnpj_cpf and int(
                punctuation_rm(line.partner_id.cnpj_cpf)) or '',
            'sacado_nome': line.partner_id.legal_name,
            'sacado_endereco': (
                line.partner_id.street + ' ' + line.partner_id.number),
            'sacado_bairro': line.partner_id.district or '',
            'sacado_cep':
                self.get_cep('prefixo', line.partner_id.zip),
            'sacado_cep_sufixo':
                self.get_cep('sufixo', line.partner_id.zip),
            'sacado_cidade': line.partner_id.l10n_br_city_id.name,
            'sacado_uf': line.partner_id.state_id.code,
            'codigo_protesto':
                int(self.order.payment_mode_id.boleto_protesto),
            'prazo_protesto':
                int(self.order.payment_mode_id.boleto_protesto_prazo),
            'codigo_baixa': 2,
            'prazo_baixa': 0,  # De 5 a 120 dias.
            'controlecob_data_gravacao': self.data_hoje(),
            'cobranca_carteira':
                int(self.order.payment_mode_id.boleto_carteira),
        }

    def _prepare_pagamento(self, line):
        """
        Prepara um dict para preencher os valores do segmento A e B apartir de
        uma linha da payment.order e insere informações que irão compor o
        header do lote
        :param line: payment.line - linha que sera base para evento
        :return: dict - Dict contendo todas informações dos segmentos
        """
        vals = {

            # SEGMENTO A
            # CONTROLE
            # 01.3A
            'controle_banco':
                int(self.order.company_partner_bank_id.code_bc),
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
            'servico_tipo_movimento': self.order.tipo_movimento,
            # 07.3A
            'servico_codigo_movimento': self.order.codigo_instrucao_movimento,

            # FAVORECIDO
            # 08.3A - 018-TED 700-DOC
            'favorecido_camara': 0,
            # 09.3A
            'favorecido_banco': int(line.bank_id.code_bc),
            # 10.3A
            'favorecido_agencia': int(line.bank_id.bra_number),
            # 11.3A
            'favorecido_agencia_dv': line.bank_id.bra_number_dig,
            # 12.3A
            'favorecido_conta': punctuation_rm(line.bank_id.acc_number),
            # 13.3A
            'favorecido_conta_dv': line.bank_id.acc_number_dig[0]
            if line.bank_id.acc_number_dig else '',
            # 14.3A
            'favorecido_dv': line.bank_id.acc_number_dig[1]
            if len(line.bank_id.bra_number_dig or '') > 1 else '',
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
            # 'credito_nosLoteso_numero': '',
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

            # SEGMENTO B
            # Preenchido no segmento A
            # 01.3B
            # 02.3B
            # 03.3B

            # 04.3B
            # 05.3B
            # 06.3B

            # DADOS COMPLEMENTARES - FAVORECIDOS
            # 07.3B
            'favorecido_tipo_inscricao':
                self.get_inscricao_tipo(line.partner_id),
            # 08.3B
            'favorecido_num_inscricao': line.partner_id.cnpj_cpf and
                int(punctuation_rm(line.partner_id.cnpj_cpf)) or '',
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
            # 'favorecido_cep': int(line.partner_id.zip[:5]) or 0,
            'favorecido_cep': self.get_cep('prefixo', line.partner_id.zip),
            # 15.3B
            'favorecido_cep_complemento':
                self.get_cep('sufixo', line.partner_id.zip),
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

    def _adicionar_evento(self, line):
        """
        Adicionar o evento no arquivo de acordo com seu tipo
        """
        # if self.order.payment_order_type == 'payment':
        #     incluir = self.arquivo.incluir_debito_pagamento
        #     prepare = self._prepare_pagamento
        # else:
        #     incluir = self.arquivo.incluir_cobranca
        #     prepare = self._prepare_cobranca
        pass

    def remessa(self, order):
        """
        Cria a remessa de eventos que sera anexada ao arquivo
        :param order: payment.order
        :return: Arquivo Cnab pronto para download
        """
        # cobrancasimples_valor_titulos = 0

        self.order = order

        # Preparar Header do Arquivo
        self.arquivo = Arquivo(self.bank, **self._prepare_header())

        if order.payment_order_type == 'payment':
            incluir = self.arquivo.incluir_debito_pagamento
            prepare = self._prepare_pagamento

            header = self.bank.registros.HeaderLotePagamento(
                **self._prepare_header_lote())

            trailer = self.bank.registros.TrailerLotePagamento()
            trailer.somatoria_valores = Decimal('0.00')
            trailer.somatoria_quantidade_moedas = Decimal('0.00000')

            lote_pagamento = Lote(self.bank, header, trailer)
            self.arquivo.adicionar_lote(lote_pagamento)

        else:
            incluir = self.arquivo.incluir_cobranca
            prepare = self._prepare_cobranca

        for line in order.bank_line_ids:
            # para cada linha da payment order adicoinar como um novo evento
            # self._adicionar_evento(line)
            # try:
            incluir(tipo_lote=30, **prepare(line))
            # except:
            #     from odoo import exceptions
            #     raise exceptions.ValidationError("Erro")
            # self.arquivo.lotes[0].header.servico_servico = 30
            # TODO: tratar soma de tipos de cobranca
            # cobrancasimples_valor_titulos += line.amount_currency
            # self.arquivo.lotes[0].trailer.cobrancasimples_valor_titulos = \
            #     Decimal(cobrancasimples_valor_titulos).quantize(
            #         Decimal('1.00'))

        remessa = unicode(self.arquivo)
        return unicodedata.normalize(
            'NFKD', remessa).encode('ascii', 'ignore')

    def get_cep(self, tipo, value):
        '''
        :param tipo:
        :param value:
        :return:
        '''
        if not value:
            if tipo == 'prefixo':
                return 0
            else:
                return ''
        value = punctuation_rm(value)
        sufixo = value[-3:]
        prefixo = value[:5]
        if tipo == 'sufixo':
            return sufixo
        else:
            return prefixo

    def format_date(self, srt_date):
        if not srt_date:
            return 0
        return int(datetime.datetime.strptime(
            srt_date, '%Y-%m-%d').strftime('%d%m%Y'))

    def data_hoje(self):
        return (int(time.strftime("%d%m%Y")))

    def hora_agora(self):
        return (int(time.strftime("%H%M%S")))

    def nosso_numero(self, format):
        """
        Hook para ser sobrescrito e adicionar informação
        :param format:
        :return:
        """
        pass
