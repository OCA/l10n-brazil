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
from pyboleto.data import BoletoData
import datetime
import re
import string
import unicodedata
import time
from openerp.exceptions import Warning as UserError

TIPO_CONTA_FORNECEDOR = [
    ('1', u'Conta corrente'),
    ('2', u'Conta Poupança'),
]

TIPO_DOCUMENTO = [
    ('01', u'Nota Fiscal/Fatura'),
    ('02', u'Fatura'),
    ('03', u'Nota Fiscal'),
    ('01', u'Duplicata'),
    ('01', u'Outros'),
]

MODALIDADE = [
    ('01', u'01 - Crédito em conta-corrente ou poupança Bradesco'),
    ('02', u'02 - Cheque OP ( Ordem de Pagamento'),
    ('03', u'03 - DOC COMPE'),
    ('05', u'05 - Crédito em conta real time'),
    ('08', u'08 - TED'),
    ('30', u'30 - Rastreamento de Títulos'),
    ('31', u'31 - Títulos de terceiros'),
]

TIPO_MOVIMENTO = [
    ('0', u'Inclusão'),
    ('5', u'Alteração'),
    ('9', u'Exclusão'),
]

CODIGO_MOVIMENTO = [
    ('00', u'Autoriza agendamento'),
    ('25', u'Desautoriza Agendamento'),
    ('50', u'Efetuar Alegçação'),
]

TIPO_DOC = [
    ('C', u'Titularidade Diferente'),
    ('D', u'Mesma Titularidade'),
]

FINALIDADE_DOC_TED = [
    ('01', u'Crédito em Conta Corrente'),
    ('02', u'Pagamento de Aluguel /Condomínios'),
    ('03', u'Pagamento de Duplicatas/Títulos'),
    ('04', u'Pagamento de Dividendos'),
    ('05', u'Pagamento de Mensal. Escolares'),
    ('06', u'Pagamento de Salário'),
    ('07', u'Pagamento de Fornec/Honor.'),
    ('08', u'Operações de Câmbio /Fundos /Bolsa de Valores'),
    ('09', u'Repasse de Arrec./Pagto de Tributos'),
    ('10', u'Transferência Internacional em Reais'),
    ('11', u'DOC COMPE/TED para Poupança'),
    ('12', u'DOC COMPE/TED para Depósito Judicial'),
    ('13', u'Pensão Alimentícia'),
    ('14', u'Restituição de Imposto de Renda'),
    ('18', u'Operações Seguro Habit.', u'SFH'),
    ('19', u'Operações do FDS', u'Caixa'),
    ('20', u'Pagamento De Operação De Crédito'),
    ('23', u'Taxa de Administração'),
    ('27', u'Pagamento Acordo/Execução Judicial'),
    ('28', u'Liquidação de Empréstimos Consignados'),
    ('29', u'Pagamento de Bolsa Auxilio'),
    ('30', u'Remuneração A Cooperado'),
    ('31', u'Pagamento de Prebenda'),
    ('33', u'Pagamento de Juros sobre Capital Próprio'),
    ('34', u'Pagamento de Rendimentos ou Amortização s/ Cotas '
           u'e/ou Debêntures'),
    ('35', u'Taxa De Serviço'),
    ('37', u'Pagamento de Juros e/ou Amortização de Títulos '
           u'Depositados em Garantia.'),
    ('38', u'Estorno Ou Restituição', u'Diversos'),
    ('59', u'Restituição de Prêmios de Seguros'),
    ('60', u'Pagamento de Indenização Sinistro Seguro'),
    ('61', u'Pagamento de Premio de Co-Seguro'),
    ('63', u'Pagamento de Indenização Sinistro Co-Seguro'),
    ('64', u'Pagamento de Premio De Resseguro'),
    ('65', u'Restituição de Premio De Resseguro'),
    ('66', u'Pagamento de Indenização Sinistro Resseguro'),
    ('67', u'Restituição Indenização Sinistro Resseguro'),
    ('68', u'Pagamento de Despesas Com Sinistro'),
    ('69', u'Pagamento de Inspeções/Vistorias Prévias'),
    ('70', u'Pagamento de Resgate de Titulo de Capitalização'),
    ('71', u'Pagamento de Sorteio de Titulo de Capitalização'),
    ('72', u'Devolução Mensal de Titulo de Capitalização.'),
    ('73', u'Restituição de Contribuição de Plano Previdenciário'),
    ('74', u'Pagamento de Beneficio Previdenciário Pecúlio'),
    ('75', u'Pagamento de Beneficio Previdenciário Pensão'),
    ('76', u'Pagamento de Beneficio Previdenciário Aposentadoria'),
    ('77', u'Pagamento de Resgate Previdenciário'),
    ('78', u'Pagamento de Comissão de Corretagem'),
    ('79', u'Pagamento de Transferências/Portabilidade de Reserva '
           u'Seguro/Previdência'),
    ('80', u'Pagamento de Impostos'),
    ('81', u'Pagamento de Serviços Públicos'),
    ('82', u'Pagamento de Honorários'),
    ('83', u'Pagamento de Corretoras'),
    ('84', u'Repasse de Valores BNDES'),
    ('85', u'Liquidação de Compromissos com BNDES'),
    ('86', u'Compra e Venda de Ações'),
    ('87', u'Contratos Referenciados em Ações ou Índices de Ações'),
    ('88', u'Operação De Cambio'),
    ('89', u'Pagamento de Boleto Bancário em Cartório'),
    ('90', u'Pagamento de Tarifas pela Prestação de Serviços de Arrecadação'
           u' de Convênios'),
    ('91', u'Operações no Mercado de Renda Fixa e Variável com Utilização '
           u'de Intermediário'),
    ('92', u'Operação de Câmbio Mercado Interbancário Instituições '
           u'sem Reservas Bancárias'),
    ('93', u'Pagamento de Operações com Identificação de Destinatário Final'),
    ('94', u'Ordem Bancaria do Tesouro - OBT'),
    ('99', u'Outros'),
]

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
            'arquivo_data_de_geracao': self.data_hoje_pag_for(),
            'arquivo_hora_de_geracao': self.hora_agora(),
            # TODO: Número sequencial de arquivo
            'numero_remessa': int(self.get_file_numeration()),
            'cedente_inscricao_tipo': self.inscricao_tipo,
            'cnpj_cpf_base': int(punctuation_rm(
                self.order.company_id.cnpj_cpf)[0:8]),
            'cnpj_cpf_filial': int(punctuation_rm(
                self.order.company_id.cnpj_cpf)[9:12]),
            'sufixo_cnpj': int(punctuation_rm(
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

    def format_date_ano_mes_dia(self, srt_date):
        return int(datetime.datetime.strptime(
            srt_date, '%Y-%m-%d').strftime('%Y%m%d'))

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

    def _prepare_segmento(self, line, vals):
        """

        :param line:
        :return:
        """
        segmento = {}

        vals.update(segmento)

        # TODO this zip code
        prefixo, sulfixo = self.cep(line.partner_id.zip)

        aceite = u'N'
        if not self.order.mode.boleto_aceite == 'S':
            aceite = u'A'

        segmento =  {
            'conta_complementar': int(self.order.mode.bank_id.acc_number),
            # 'especie_titulo': 8,

            'tipo_inscricao': int(
                self.sacado_inscricao_tipo(line.partner_id)),
            'cnpj_cpf_base_forn': int(
                self.rmchar(line.partner_id.cnpj_cpf)[0:8]),
            'cnpj_cpf_filial_forn': int(
                self.rmchar(line.partner_id.cnpj_cpf)[9:12]),
            'cnpj_cpf_forn_sufixo': int(
                self.rmchar(line.partner_id.cnpj_cpf)[12:14]),
            'nome_forn': line.partner_id.legal_name,
            'endereco_forn': (
                line.partner_id.street + ' ' + line.partner_id.number),
            'cep_forn': int(prefixo),
            'cep_complemento_forn': int(sulfixo),


            # 'nosso_numero': 11,  # FIXME # TODO quando banco é 237, deve-se extrair da linha digitável. Do contrário, zeros.

            # 'numero_documento': line.name,
            # 'vencimento_titulo': self.format_date_ano_mes_dia(
            #     line.ml_maturity_date),

            'data_emissao_titulo': self.format_date_ano_mes_dia(
                line.ml_date_created),

            'desconto1_data': 0,
            'fator_vencimento': 0,  # FIXME

            'valor_titulo': Decimal(str(line.amount_currency)).quantize(
                Decimal('1.00')),

            'valor_pagto': Decimal(str(line.amount_currency)).quantize(
                Decimal('1.00')),

            'valor_desconto': Decimal('0.00'),

            'valor_acrescimo': Decimal('0.00'),

            # FIXME
            'tipo_documento': 2, # NF, Fatura, Duplicata...
            # NF_Fatura_01/Fatura_02/NF_03/Duplicata_04/Outros_05
            'numero_nf': int(line.ml_inv_ref.internal_number),

            'modalidade_pagamento': int(line.order_id.mode.type_purchase_payment),

            'data_para_efetivacao_pag': 0,  # Quando não informada o sistema assume a data constante do campo Vencimento

            'tipo_movimento': 0,
            # TODO Tipo de Movimento.
            # 0 - Inclusão.
            # 5 - Alteração.
            # 9 - Exclusão.

            'codigo_movimento': 0,  # Autoriza agendamento

            # 'horario_consulta_saldo': u'5',  # Quando não informado consulta em todos processamentos



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
        segmento.update(vals)
        return segmento

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
            self.arquivo.incluir_pagamento(**self.incluir_pagamento_for(line))
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

    def data_hoje_pag_for(self):
        return (int(time.strftime("%Y%m%d")))

    def hora_agora(self):
        return (int(time.strftime("%H%M%S")))

    @staticmethod
    def modulo11(num, base, r):
        return BoletoData.modulo11(num, base=9, r=0)

    def incluir_pagamento_for(self, line):
        mode = line.order_id.mode.type_purchase_payment
        if mode in ('01'):
            return self.lancamento_credito_bradesco(line)
        elif mode in ('02'):
            raise UserError('Operação não suportada')
        elif mode in ('03'):
            return self.lancamento_doc(line)
        elif mode in ('05'):
            raise UserError('Operação não suportada')
        elif mode in ('08'):
            return self.lancamento_ted(line)
        elif mode in ('30'):
            raise UserError('Operação não suportada')
        elif mode in ('31'):
            # titulos de terceiros
            return self.lancamento_titulos_terceiros(line)
        raise UserError('Operação não suportada')

    def lancamento_credito_bradesco(self, line):
        # TODO:
        # modalidade 01.

        vals = {
            'especie_titulo': line.order_id.mode.type_purchase_payment,

            'codigo_banco_forn': 237,
            'codigo_agencia_forn': int(line.bank_id.bra_number),
            'digito_agencia_forn_transacao': line.bank_id.bra_number_dig,
            'conta_corrente_forn': int(line.bank_id.acc_number),
            'digito_conta_forn_transacao': line.bank_id.acc_number_dig,

            'numero_pagamento':
                self.adiciona_digitos_num_pag(line.communication),

            'carteira': int(self.order.mode.boleto_carteira),

            'nosso_numero': 0,

            'vencimento_titulo': self.format_date_ano_mes_dia(
                line.ml_maturity_date),

            'informacoes_complementares': u'',
        }

        return self._prepare_segmento(line, vals)


    def lancamento_ted(self, line):
        # TODO:
        # modalidade 08.

        vals =  {
            'conta_complementar': int(self.order.mode.bank_id.acc_number),
            'especie_titulo': line.order_id.mode.type_purchase_payment,


            # TODO: código do banco. Para a Modalidade de Pagamento valor
            # pode variar
            'codigo_banco_forn': int(line.bank_id.bank.bic),
            'codigo_agencia_forn': int(line.bank_id.bra_number),
            'digito_agencia_forn_transacao': line.bank_id.bra_number_dig,
            'conta_corrente_forn': int(line.bank_id.acc_number),
            'digito_conta_forn_transacao': line.bank_id.acc_number_dig,
            # TODO Gerado pelo cliente pagador quando do agendamento de
            # pagamento por parte desse, exceto para a modalidade 30 -
            # Títulos em Cobrança Bradesco
            # communication
            'numero_pagamento':
                self.adiciona_digitos_num_pag(line.communication),

            'carteira': 0,

            'nosso_numero': 0,

            'vencimento_titulo': self.format_date_ano_mes_dia(
                line.ml_maturity_date),

            'fator_vencimento': 0,  # FIXME

            # 'modalidade_pagamento': int(self.order.mode.boleto_especie),

            'tipo_movimento': 0,
            # TODO Tipo de Movimento.
            # 0 - Inclusão.
            # 5 - Alteração.
            # 9 - Exclusão. Wkf Odoo.
            'codigo_movimento': 0,  # FIXME
            # 'horario_consulta_saldo': u'5',  # FIXME

            # 'informacoes_complementares': self.montar_info_comple_ted(),
            'informacoes_complementares': u'',

            'codigo_lancamento': 0,  # FIXME
            'tipo_conta_fornecedor': 1,  # FIXME

        }

        return self._prepare_segmento(line, vals)

    def lancamento_doc(self):
        # TODO:

        vals =  {}

        return self._prepare_segmento(vals)

    def lancamento_titulos_terceiros(self, line):
        # TODO:

        res_cods_ag_cc = \
            self.ler_linha_digitavel_codigos_ag_cc(line.linha_digitavel)

        vals = {
            'conta_complementar': int(self.order.mode.bank_id.acc_number),
            'especie_titulo': line.order_id.mode.type_purchase_payment,

            # extrair do código de barras
            'codigo_banco_forn': res_cods_ag_cc['codigo_banco_forn'],
            'codigo_agencia_forn': res_cods_ag_cc['codigo_agencia_forn'],
            'digito_agencia_forn_transacao':
                res_cods_ag_cc['digito_agencia_forn_transacao'],
            'conta_corrente_forn': res_cods_ag_cc['conta_corrente_forn'],
            'digito_conta_forn_transacao':
                res_cods_ag_cc['digito_conta_forn_transacao'],

            'carteira': res_cods_ag_cc['carteira']

        }

        return self._prepare_segmento(vals)

    def adiciona_digitos_num_pag(self, campo):
        num_digitos = 16
        campo = str(campo)
        chars_faltantes = num_digitos - len(campo)
        return (u' ' * chars_faltantes) + campo

    def montar_info_comple_ted(self):
        tipo_doc_compe = TIPO_DOC[0][0]
        num_doc_ted = '000000'
        finalidade_doc_compe = FINALIDADE_DOC_TED[2][0] # pagamento duplicatas. Ou será 01?
        tipo_conta_doc_ted = '01'
        codigo_identif_transf = '0000000000000000000000000'
        fim_do_campo = '    '
        info_comple = tipo_doc_compe + num_doc_ted + finalidade_doc_compe + \
                      tipo_conta_doc_ted + codigo_identif_transf + fim_do_campo
        return (info_comple.encode('utf-8'))

    def ler_linha_digitavel_codigos_ag_cc(self, linha_digitavel):
        linha_completa = linha_digitavel

        codigo_banco_fornecedor = linha_digitavel[:3]
        res = {}

        # para banco = 237, bradesco
        if (codigo_banco_fornecedor == '237'):
            res = {
                'codigo_banco_forn': int(codigo_banco_fornecedor),
                'codigo_agencia_forn': int(linha_digitavel[4:8]),
                'digito_agencia_forn_transacao': u'',  # Calcular usando modulo 11 base 7
                'conta_corrente_forn': int(linha_digitavel[23:30]),
                'digito_conta_forn_transacao': u'',  # Calcular usando modulo 11 base 7

                'carteira': int(linha_digitavel[8:10]),

                'nosso_numero': int(linha_digitavel[11:21])
            }
        # para outros bancos
        else:
            res = {
                'codigo_banco_forn': int(codigo_banco_fornecedor),
                'codigo_agencia_forn': 0,
                'digito_agencia_forn_transacao': u'',
                'conta_corrente_forn': 0,
                'digito_conta_forn_transacao': u'',

                'carteira': 0,

                'nosso_numero': 0,
            }
        return res
