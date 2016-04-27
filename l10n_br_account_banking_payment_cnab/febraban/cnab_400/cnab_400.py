# coding: utf-8
# ###########################################################################
#
#    Author: Fernando Marcato Rodrigues
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
from cnab240.tipos import ArquivoCobranca400
from decimal import Decimal
from openerp import api, models, fields, _
from openerp.addons.l10n_br_base.tools.misc import punctuation_rm
import datetime
import re
import string
import unicodedata
import time

IDENTIFICACAO_DA_OCORRENCIA = [
    ('01', u'Remessa'),
    ('02', u'Pedido de baixa'),
    ('03', u'Pedido de Protesto Falimentar'),
    ('04', u'Concessão de abatimento'),
    ('05', u'Cancelamento de abatimento concedido'),
    ('06', u'Alteração de vencimento'),
    ('07', u'Alteração do controle do participante'),
    ('08', u'Alteração de seu número'),
    ('09', u'Pedido de protesto'),
    ('18', u'Sustar protesto e baixar Título'),
    ('19', u'Sustar protesto e manter em carteira'),
    ('22', u'Transferência Cessão crédito ID. Prod.10'),
    ('23', u'Transferência entre Carteiras'),
    ('24', u'Dev. Transferência entre Carteiras'),
    ('31', u'Alteração de outros dados'),
    ('45', u'Pedido de Negativação (NOVO)'),
    ('46', u'Excluir Negativação com baixa (NOVO)'),
    ('47', u'Excluir negativação e manter pendente (NOVO)'),
    ('68', u'Acerto nos dados do rateio de Crédito'),
    ('69', u'Cancelamento do rateio de crédito'),
]

ESPECIE_DE_TITULO = [
    ('01', u'Duplicata'),
    ('02', u'Nota Promissória'),
    ('03', u'Nota de Seguro'),
    ('04', u'Cobrança Seriada'),
    ('05', u'Recibo'),
    ('10', u'Letras de Câmbio'),
    ('11', u'Nota de Débito'),
    ('12', u'Duplicata de Serv'),
    ('30', u'Boleto de Proposta'),
    ('99', u'Outros'),
]

# Essas instruções deverão ser enviadas no Arquivo-Remessa, quando da entrada, desde que código de ocorrência na posição 109 a 110 do registro de transação, seja “01”, para as instruções de protesto/negativação, o CNPJ / CPF e o endereço do Pagador deverão ser informados corretamente
LISTA_PRIMEIRA_INSTRUCAO = [
    ('05', u'Protesto Falimentar'),
    ('06', u'Protestar'),
    ('07', u'Negativar'),
    ('18', u'Decurso de prazo'),

    ('08', u'Não cobrar juros de mora'),
    ('09', u'Não receber após o vencimento'),
    ('10', u'Multas de 10% após o 4o dia do Vencimento'),
    ('11', u'Não receber após o 8o dia do vencimento.'),
    ('12', u'Cobrar encargos após o 5o dia do vencimento'),
    ('13', u'Cobrar encargos após o 10o dia do vencimento'),
    ('14', u'Cobrar encargos após o 15o dia do vencimento'),
    ('15', u'Conceder desconto mesmo se pago após o vencimento'),
]



class Cnab400(Cnab):

    def __init__(self):
        super(Cnab, self).__init__()

    @staticmethod
    def get_bank(bank):
        if bank == '237':
            from .bancos.bradesco import Bradesco400
            return Bradesco400
        else:
            return Cnab400

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
            'arquivo_codigo': 1,  # Remessa/Retorno
            'servico_operacao': u'R',
            'nome_banco': unicode(self.order.mode.bank_id.bank_name),
            'codigo_empresa': int(self.order.mode.boleto_convenio),
        }

    def get_file_numeration(self):
        numero = self.order.get_next_number()
        if not numero:
            numero = 1
        return numero

    def format_date(self, srt_date):
        return int(datetime.datetime.strptime(
            srt_date, '%Y-%m-%d').strftime('%d%m%y'))

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

    def codificar(self, texto):
        return texto.encode('utf-8')

    def _prepare_segmento(self, line):
        """
        :param line:
        :return:
        """
        prefixo, sulfixo = self.cep(line.partner_id.zip)

        aceite = u'N'
        if not self.order.mode.boleto_aceite == 'S':
            aceite = u'A'

        codigo_protesto = 0
        dias_protestar = 0
        if self.order.mode.boleto_protesto == '3' \
                or self.order.mode.boleto_protesto == '0':
            codigo_protesto = 0
            dias_protestar = 0
        elif self.order.mode.boleto_protesto == '1' \
                or self.order.mode.boleto_protesto == '2':
            codigo_protesto = 6
            if (int(self.order.mode.boleto_protesto_prazo)) < 5:
                dias_protestar = 5
            else:
                dias_protestar = int(self.order.mode.boleto_protesto_prazo)

        sacado_endereco = self.retorna_endereco(line.partner_id.id)


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

            'percentual_multa': Decimal('0.00'),
            'valor_desconto': Decimal('0.00'),
            'valor_abatimento_concedido_cancelado': Decimal('0.00'),
            'primeira_instrucao': codigo_protesto,
            'segunda_instrucao': dias_protestar,
            'sacado_cep': int(prefixo),
            'sacado_cep_sufixo': int(sulfixo),
            'sacador_avalista': self.order.mode.comunicacao_2,
            # 'sacador_avalista': u'Protestar após 5 dias',
            'num_seq_registro': self.controle_linha,

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

            'vencimento_titulo': self.format_date(
                line.ml_maturity_date),
            'valor_titulo': Decimal(str(line.amount_currency)).quantize(
                Decimal('1.00')),
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

            # 'juros_mora_taxa_dia': Decimal('0.20'),
            'juros_mora_taxa_dia':
                self.calcula_valor_juros_dia(
                    line.amount_currency, line.percent_interest),

            'valor_abatimento': Decimal('0.00'),
            'sacado_inscricao_tipo': int(
                self.sacado_inscricao_tipo(line.partner_id)),
            'sacado_inscricao_numero': int(
                self.rmchar(line.partner_id.cnpj_cpf)),
            'sacado_nome': line.partner_id.legal_name,

            # 'sacado_endereco': (
            #     line.partner_id.street +
            #     ' ' + str(line.partner_id.number)
            # ),

            'sacado_endereco': sacado_endereco,

            'sacado_bairro': line.partner_id.district,
            'sacado_cidade': line.partner_id.l10n_br_city_id.name,
            'sacado_uf': line.partner_id.state_id.code,
            'codigo_baixa': 2,
            'prazo_baixa': 0,  # De 5 a 120 dias.
            'controlecob_data_gravacao': self.data_hoje(),
            'cobranca_carteira': int(self.order.mode.boleto_carteira),

            'primeira_mensagem': u'',

            'identificacao_ocorrencia': 1, # Trazer da nova tela do payment_mode

            # numero fatura esta copiando para communication
            'numero_documento':
                self.adiciona_digitos_num_doc(line.communication),
            # 'numero_documento': str(line.move_line_id.invoice.number),

        }

    def remessa(self, order):
        """

        :param order:
        :return:
        """
        cobrancasimples_valor_titulos = 0

        self.order = order
        self.arquivo = ArquivoCobranca400(self.bank, **self._prepare_header())
        for line in order.line_ids:
            self.arquivo.incluir_cobranca(**self._prepare_segmento(line))
            self.arquivo.trailer.num_seq_registro = self.controle_linha

        remessa = unicode(self.arquivo)
        return unicodedata.normalize(
            'NFKD', remessa).encode('ascii', 'ignore')

    def data_hoje(self):
        return (int(time.strftime("%d%m%y")))

    def hora_agora(self):
        return (int(time.strftime("%H%M%S")))

    def calcula_valor_juros_dia(self, total_titulo, percent_juros):
        valor_juros = 0
        valor_juros = (total_titulo * (percent_juros / 100))
        return (Decimal(valor_juros).quantize(Decimal('1.00')))

    def adiciona_digitos_num_doc(self, campo):
        num_digitos = 10
        campo = str(campo)
        chars_faltantes = num_digitos - len(campo)
        return (u' ' * chars_faltantes) + campo

    # @api.multi
    def retorna_endereco(self, id_parceiro):
        # self.ensure_one()
        # workaround to get env
        res_partner_model = self.order.env['res.partner']
        res_partner_end_cobranca = res_partner_model.search(
            [('parent_id', '=', id_parceiro), ('type', '=', 'cnab_cobranca')],
            limit=1)
        if res_partner_end_cobranca:
            str_endereco = self.monta_endereco(res_partner_end_cobranca)
        else:
            res_partner_end_cobranca = res_partner_model.search(
                [('id', '=', id_parceiro)]
            )
            str_endereco = self.monta_endereco(res_partner_end_cobranca)
            # Essa abordagem substitui caracteres especiais por '?'
            # str_endereco = unicode(str_endereco.encode("ascii", errors="replace"))

        # Substitui sinal de grau por espaço
        str_endereco = str_endereco.replace(u"\xb0", u" ")

        return str_endereco

    def monta_endereco(self, partner_item):

        street = self.check_address_item_filled(partner_item.street)
        number = self.check_address_item_filled(partner_item.number)
        complemento = self.check_address_item_filled(partner_item.street2)
        distrito = self.check_address_item_filled(partner_item.district)

        str_endereco = (
            street
            + ' ' +
            number
            + ' ' +
            complemento
            + ' ' +
            distrito
            # + ' ' +
            # partner_item.l10n_br_city_id.name + \
            # '  ' + partner_item.state_id.name
        )
        return str_endereco

    def check_address_item_filled(self, item):
        if item == False:
            return ('')
        else:
            return item
