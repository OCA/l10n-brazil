# -*- coding: utf-8 -*-
# © 2012 KMEE INFORMATICA LTDA
#   @author  Luiz Felipe do Divino Costa <luiz.divino@kmee.com.br>
#   @author  Luis Felipe Mileo <mileo@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
import re
from datetime import datetime
from ..constantes import CODIGO_OCORRENCIAS
from ..febraban.cnab import Cnab
from odoo.exceptions import UserError

from odoo import api, models, fields

_logger = logging.getLogger(__name__)

STATE = [
    ('draft', 'Novo'),
    ('done', 'Processado'),
    ('error', 'Erro no Processamento')
]

TIPO_OPERACAO = {
    'C': u'Lançamento a Crédito',
    'D': u'Lançamento a Débito',
    'E': u'Extrato para Conciliação',
    'G': u'Extrato para Gestão de Caixa',
    'I': u'Informações de Títulos Capturados do Próprio Banco',
    'R': u'Arquivo Remessa',
    'T': u'Arquivo Retorno',
}

TIPO_SERVICO = {
    '01': 'Cobrança',
    '03': 'Boleto de Pagamento Eletrônico',
    '04': 'Conciliação Bancária',
    '05': 'Débitos',
    '06': 'Custódia de Cheques',
    '07': 'Gestão de Caixa',
    '08': 'Consulta/Informação Margem',
    '09': 'Averbação da Consignação/Retenção',
    '10': 'Pagamento Dividendos',
    '11': 'Manutenção da Consignação',
    '12': 'Consignação de Parcelas',
    '13': 'Glosa da Consignação (INSS)',
    '14': 'Consulta de Tributos a pagar',
    '20': 'Pagamento Fornecedor',
    '22': 'Pagamento de Contas, Tributos e Impostos',
    '23': 'Interoperabilidade entre Contas de Instituições de Pagamentos',
    '25': 'Compror',
    '26': 'Compror Rotativo',
    '29': 'Alegação do Pagador',
    '30': 'Pagamento Salários',
    '32': 'Pagamento de honorários',
    '33': 'Pagamento de bolsa auxílio',
    '34': 'Pagamento de prebenda (remuneração a padres e sacerdotes)',
    '40': 'Vendor',
    '41': 'Vendor a Termo',
    '50': 'Pagamento Sinistros Segurados',
    '60': 'Pagamento Despesas Viajante em Trânsito',
    '70': 'Pagamento Autorizado',
    '75': 'Pagamento Credenciados',
    '77': 'Pagamento de Remuneração',
    '80': 'Pagamento Representantes / Vendedores Autorizados',
    '90': 'Pagamento Benefícios',
    '98': 'Pagamentos Diversos',
}

TIPO_INSCRICAO_EMPRESA = {
    0: 'Isento / Não informado',
    1: 'CPF',
    2: 'CGC / CNPJ',
    3: 'PIS / PASEP',
    9: 'Outros',
}


RETORNO_400_CONFIRMADA = [
    2,
]

RETORNO_400_REJEITADA = [
    3,
]

RETORNO_400_LIQUIDACAO = [
    6,
    # 7, TODO: Implementar a baixa parcial;
    8,
]

RETORNO_400_BAIXA = [
    9,
    10,
]

RETORNOS_TRATADOS = \
    [RETORNO_400_CONFIRMADA, RETORNO_400_REJEITADA, RETORNO_400_LIQUIDACAO, RETORNO_400_BAIXA]

# COD_REGISTROS_REJEITADOS_CNAB400 -> USADO QUANDO HA CODIGO DE OCORRENCIA 03 NA POSIÇÃO 109-110
COD_REGISTROS_REJEITADOS_CNAB400 = {
    3: 'AG. COBRADORA - CEP SEM ATENDIMENTO DE PROTESTO NO MOMENTO',
    4: 'ESTADO - SIGLA DO ESTADO INVÁLIDA',
    5: 'DATA VENCIMENTO - PRAZO DA OPERAÇÃO MENOR QUE PRAZO MÍNIMO OU MAIOR QUE O MÁXIMO',
    7: 'VALOR DO TÍTULO - VALOR DO TÍTULO MAIOR QUE 10.000.000,00',
    8: 'NOME DO PAGADOR - NÃO INFORMADO OU DESLOCADO',
    9: 'AGENCIA/CONTA - AGÊNCIA ENCERRADA',
    10: 'LOGRADOURO - NÃO INFORMADO OU DESLOCADO',
    11: 'CEP - CEP NÃO NUMÉRICO OU CEP INVÁLIDO',
    12: 'SACADOR / AVALISTA - NOME NÃO INFORMADO OU DESLOCADO (BANCOS CORRESPONDENTES)',
    13: 'ESTADO/CEP - CEP INCOMPATÍVEL COM A SIGLA DO ESTADO',
    14: 'NOSSO NÚMERO - NOSSO NÚMERO JÁ REGISTRADO NO CADASTRO DO BANCO OU FORA DA FAIXA',
    15: 'NOSSO NÚMERO - NOSSO NÚMERO EM DUPLICIDADE NO MESMO MOVIMENTO',
    18: 'DATA DE ENTRADA - DATA DE ENTRADA INVÁLIDA PARA OPERAR COM ESTA CARTEIRA',
    19: 'OCORRÊNCIA - OCORRÊNCIA INVÁLIDA',
    21: 'AG. COBRADORA - CARTEIRA NÃO ACEITA DEPOSITÁRIA CORRESPONDENTE ESTADO DA AGÊNCIA DIFERENTE DO ESTADO DO PAGADOR AG. COBRADORA NÃO CONSTA NO CADASTRO OU ENCERRANDO',
    22: 'CARTEIRA - CARTEIRA NÃO PERMITIDA (NECESSÁRIO CADASTRAR FAIXA LIVRE)',
    26: 'AGÊNCIA/CONTA - AGÊNCIA/CONTA NÃO LIBERADA PARA OPERAR COM COBRANÇA',
    27: 'CNPJ INAPTO - CNPJ DO BENEFICIÁRIO INAPTO DEVOLUÇÃO DE TÍTULO EM GARANTIA',
    29: 'CÓDIGO EMPRESA - CATEGORIA DA CONTA INVÁLIDA',
    30: 'ENTRADA BLOQUEADA - ENTRADAS BLOQUEADAS, CONTA SUSPENSA EM COBRANÇA',
    31: 'AGÊNCIA/CONTA - CONTA NÃO TEM PERMISSÃO PARA PROTESTAR (CONTATE SEU GERENTE)',
    35: 'VALOR DO IOF - IOF MAIOR QUE 5%',
    36: 'QTDADE DE MOEDA - QUANTIDADE DE MOEDA INCOMPATÍVEL COM VALOR DO TÍTULO',
    37: 'CNPJ/CPF DO PAGADOR - NÃO NUMÉRICO OU IGUAL A ZEROS',
    42: 'NOSSO NÚMERO - NOSSO NÚMERO FORA DE FAIXA',
    52: 'AG. COBRADORA - EMPRESA NÃO ACEITA BANCO CORRESPONDENTE',
    53: 'AG. COBRADORA - EMPRESA NÃO ACEITA BANCO CORRESPONDENTE - COBRANÇA MENSAGEM',
    54: 'DATA DE VENCTO - BANCO CORRESPONDENTE - TÍTULO COM VENCIMENTO INFERIOR A 15 DIAS',
    55: 'DEP/BCO CORRESP - CEP NÃO PERTENCE À DEPOSITÁRIA INFORMADA',
    56: 'DT VENCTO/BCO CORRESP - VENCTO SUPERIOR A 180 DIAS DA DATA DE ENTRADA',
    57: 'DATA DE VENCTO - CEP SÓ DEPOSITÁRIA BCO DO BRASIL COM VENCTO INFERIOR A 8 DIAS',
    60: 'ABATIMENTO - VALOR DO ABATIMENTO INVÁLIDO',
    61: 'JUROS DE MORA - JUROS DE MORA MAIOR QUE O PERMITIDO',
    62: 'DESCONTO - VALOR DO DESCONTO MAIOR QUE VALOR DO TÍTULO',
    63: 'DESCONTO DE ANTECIPAÇÃO - VALOR DA IMPORTÂNCIA POR DIA DE DESCONTO (IDD) NÃO PERMITIDO',
    64: 'DATA DE EMISSÃO - DATA DE EMISSÃO DO TÍTULO INVÁLIDA',
    65: 'TAXA FINANCTO - TAXA INVÁLIDA (VENDOR)',
    66: 'DATA DE VENCTO - INVALIDA/FORA DE PRAZO DE OPERAÇÃO (MÍNIMO OU MÁXIMO)',
    67: 'VALOR/QTIDADE - VALOR DO TÍTULO/QUANTIDADE DE MOEDA INVÁLIDO',
    68: 'CARTEIRA - CARTEIRA INVÁLIDA OU NÃO CADASTRADA NO INTERCÂMBIO DA COBRANÇA',
    69: 'CARTEIRA - CARTEIRA INVÁLIDA PARA TÍTULOS COM RATEIO DE CRÉDITO',
    70: 'AGÊNCIA/CONTA - BENEFICIÁRIO NÃO CADASTRADO PARA FAZER RATEIO DE CRÉDITO',
    78: 'AGÊNCIA/CONTA - DUPLICIDADE DE AGÊNCIA/CONTA BENEFICIÁRIA DO RATEIO DE CRÉDITO',
    80: 'AGÊNCIA/CONTA - QUANTIDADE DE CONTAS BENEFICIÁRIAS DO RATEIO MAIOR DO QUE O PERMITIDO (MÁXIMO DE 30 CONTAS POR TÍTULO)',
    81: 'AGÊNCIA/CONTA - CONTA PARA RATEIO DE CRÉDITO INVÁLIDA / NÃO PERTENCE AO ITAÚ',
    82: 'DESCONTO/ABATI-MENTO - DESCONTO/ABATIMENTO NÃO PERMITIDO PARA TÍTULOS COM RATEIO DE CRÉDITO',
    83: 'VALOR DO TÍTULO - VALOR DO TÍTULO MENOR QUE A SOMA DOS VALORES ESTIPULADOS PARA RATEIO',
    84: 'AGÊNCIA/CONTA - AGÊNCIA/CONTA BENEFICIÁRIA DO RATEIO É A CENTRALIZADORA DE CRÉDITO DO BENEFICIÁRIO',
    85: 'AGÊNCIA/CONTA - AGÊNCIA/CONTA DO BENEFICIÁRIO É CONTRATUAL / RATEIO DE CRÉDITO NÃO PERMITIDO',
    86: 'TIPO DE VALOR - CÓDIGO DO TIPO DE VALOR INVÁLIDO / NÃO PREVISTO PARA TÍTULOS COM RATEIO DE CRÉDITO',
    87: 'AGÊNCIA/CONTA - REGISTRO TIPO 4 SEM INFORMAÇÃO DE AGÊNCIAS/CONTAS BENEFICIÁRIAS DO RATEIO',
    90: 'NRO DA LINHA - COBRANÇA MENSAGEM - NÚMERO DA LINHA DA MENSAGEM INVÁLIDO OU QUANTIDADE DE LINHAS EXCEDIDAS',
    97: 'SEM MENSAGEM - COBRANÇA MENSAGEM SEM MENSAGEM (SÓ DE CAMPOS FIXOS), PORÉM COM REGISTRO DO TIPO 7 OU 8',
    98: 'FLASH INVÁLIDO - REGISTRO MENSAGEM SEM FLASH CADASTRADO OU FLASH INFORMADO DIFERENTE DO CADASTRADO',
    99: 'FLASH INVÁLIDO - CONTA DE COBRANÇA COM FLASH CADASTRADO E SEM REGISTRO DE MENSAGEM CORRESPONDENTE',
}



CODIGO_OCORRENCIAS_CNAB200 = {
    2: 'ENTRADA CONFIRMADA COM POSSIBILIDADE DE MENSAGEM (NOTA 20 – TABELA 10)',  # noqa
    3: 'ENTRADA REJEITADA (NOTA 20 – TABELA 1)', # noqa
    4: 'ALTERAÇÃO DE DADOS – NOVA ENTRADA OU ALTERAÇÃO/EXCLUSÃO DE DADOS ACATADA', # noqa
    5: 'ALTERAÇÃO DE DADOS – BAIXA',
    6: 'LIQUIDAÇÃO NORMAL',
    7: 'LIQUIDAÇÃO PARCIAL – COBRANÇA INTELIGENTE (B2B)',
    8: 'LIQUIDAÇÃO EM CARTÓRIO',
    9: 'BAIXA SIMPLES',
    10: 'BAIXA POR TER SIDO LIQUIDADO',
    11: 'EM SER (SÓ NO RETORNO MENSAL)',
    12: 'ABATIMENTO CONCEDIDO',
    13: 'ABATIMENTO CANCELADO',
    14: 'VENCIMENTO ALTERADO',
    15: 'BAIXAS REJEITADAS (NOTA 20 – TABELA 4)',
    16: 'INSTRUÇÕES REJEITADAS (NOTA 20 – TABELA 3)',
    17: 'ALTERAÇÃO/EXCLUSÃO DE DADOS REJEITADOS (NOTA 20 – TABELA 2)',
    18: 'COBRANÇA CONTRATUAL – INSTRUÇÕES/ALTERAÇÕES REJEITADAS/PENDENTES (NOTA 20 – TABELA 5)',  # noqa
    19: 'CONFIRMA RECEBIMENTO DE INSTRUÇÃO DE PROTESTO',
    20: 'CONFIRMA RECEBIMENTO DE INSTRUÇÃO DE SUSTAÇÃO DE PROTESTO /TARIFA',
    21: 'CONFIRMA RECEBIMENTO DE INSTRUÇÃO DE NÃO PROTESTAR',
    23: 'TÍTULO ENVIADO A CARTÓRIO/TARIFA',
    24: 'INSTRUÇÃO DE PROTESTO REJEITADA / SUSTADA / PENDENTE (NOTA 20 – TABELA 7)',  # noqa
    25: 'ALEGAÇÕES DO PAGADOR (NOTA 20 – TABELA 6)',
    26: 'TARIFA DE AVISO DE COBRANÇA',
    27: 'TARIFA DE EXTRATO POSIÇÃO (B40X)',
    28: 'TARIFA DE RELAÇÃO DAS LIQUIDAÇÕES',
    29: 'TARIFA DE MANUTENÇÃO DE TÍTULOS VENCIDOS',
    30: 'DÉBITO MENSAL DE TARIFAS (PARA ENTRADAS E BAIXAS)',
    32: 'BAIXA POR TER SIDO PROTESTADO',
    33: 'CUSTAS DE PROTESTO',
    34: 'CUSTAS DE SUSTAÇÃO',
    35: 'CUSTAS DE CARTÓRIO DISTRIBUIDOR',
    36: 'CUSTAS DE EDITAL',
    37: 'TARIFA DE EMISSÃO DE BOLETO/TARIFA DE ENVIO DE DUPLICATA',
    38: 'TARIFA DE INSTRUÇÃO',
    39: 'TARIFA DE OCORRÊNCIAS',
    40: 'TARIFA MENSAL DE EMISSÃO DE BOLETO/TARIFA MENSAL DE ENVIO DE DUPLICATA',  # noqa
    41: 'DÉBITO MENSAL DE TARIFAS – EXTRATO DE POSIÇÃO (B4EP/B4OX)',
    42: 'DÉBITO MENSAL DE TARIFAS – OUTRAS INSTRUÇÕES',
    43: 'DÉBITO MENSAL DE TARIFAS – MANUTENÇÃO DE TÍTULOS VENCIDOS',
    44: 'DÉBITO MENSAL DE TARIFAS – OUTRAS OCORRÊNCIAS',
    45: 'DÉBITO MENSAL DE TARIFAS – PROTESTO',
    46: 'DÉBITO MENSAL DE TARIFAS – SUSTAÇÃO DE PROTESTO',
    47: 'BAIXA COM TRANSFERÊNCIA PARA DESCONTO',
    48: 'CUSTAS DE SUSTAÇÃO JUDICIAL',
    51: 'TARIFA MENSAL REF A ENTRADAS BANCOS CORRESPONDENTES NA CARTEIRA',
    52: 'TARIFA MENSAL BAIXAS NA CARTEIRA',
    53: 'TARIFA MENSAL BAIXAS EM BANCOS CORRESPONDENTES NA CARTEIRA',
    54: 'TARIFA MENSAL DE LIQUIDAÇÕES NA CARTEIRA',
    55: 'TARIFA MENSAL DE LIQUIDAÇÕES EM BANCOS CORRESPONDENTES NA CARTEIRA',
    56: 'CUSTAS DE IRREGULARIDADE',
    57: 'INSTRUÇÃO CANCELADA (NOTA 20 – TABELA 8)',
    59: 'BAIXA POR CRÉDITO EM C/C ATRAVÉS DO SISPAG',
    60: 'ENTRADA REJEITADA CARNÊ (NOTA 20 – TABELA 1)',
    61: 'TARIFA EMISSÃO AVISO DE MOVIMENTAÇÃO DE TÍTULOS (2154)',
    62: 'DÉBITO MENSAL DE TARIFA – AVISO DE MOVIMENTAÇÃO DE TÍTULOS (2154)',
    63: 'TÍTULO SUSTADO JUDICIALMENTE',
    64: 'ENTRADA CONFIRMADA COM RATEIO DE CRÉDITO',
    65: 'PAGAMENTO COM CHEQUE – AGUARDANDO COMPENSAÇÃO',
    69: 'CHEQUE DEVOLVIDO (NOTA 20 – TABELA 9)',
    71: 'ENTRADA REGISTRADA, AGUARDANDO AVALIAÇÃO',
    72: 'BAIXA POR CRÉDITO EM C/C ATRAVÉS DO SISPAG SEM TÍTULO CORRESPONDENTE',
    73: 'CONFIRMAÇÃO DE ENTRADA NA COBRANÇA SIMPLES – ENTRADA NÃO ACEITA NA COBRANÇA CONTRATUAL',  # noqa
    74: 'INSTRUÇÃO DE NEGATIVAÇÃO EXPRESSA REJEITADA (NOTA 20 – TABELA 11)',
    75: 'CONFIRMAÇÃO DE RECEBIMENTO DE INSTRUÇÃO DE ENTRADA EM NEGATIVAÇÃO EXPRESSA',  # noqa
    76: 'CHEQUE COMPENSADO',
    77: 'CONFIRMAÇÃO DE RECEBIMENTO DE INSTRUÇÃO DE EXCLUSÃO DE ENTRADA EM NEGATIVAÇÃO EXPRESSA',  # noqa
    78: 'CONFIRMAÇÃO DE RECEBIMENTO DE INSTRUÇÃO DE CANCELAMENTO DE NEGATIVAÇÃO EXPRESSA',  # noqa
    79: 'NEGATIVAÇÃO EXPRESSA INFORMACIONAL (NOTA 20 – TABELA 12)',
    80: 'CONFIRMAÇÃO DE ENTRADA EM NEGATIVAÇÃO EXPRESSA – TARIFA',
    82: 'CONFIRMAÇÃO DO CANCELAMENTO DE NEGATIVAÇÃO EXPRESSA – TARIFA',
    83: 'CONFIRMAÇÃO DE EXCLUSÃO DE ENTRADA EM NEGATIVAÇÃO EXPRESSA POR LIQUIDAÇÃO – TARIFA', # noqa
    85: 'TARIFA POR BOLETO (ATÉ 03 ENVIOS) COBRANÇA ATIVA ELETRÔNICA',
    86: 'TARIFA EMAIL COBRANÇA ATIVA ELETRÔNICA',
    87: 'TARIFA SMS COBRANÇA ATIVA ELETRÔNICA',
    88: 'TARIFA MENSAL POR BOLETO (ATÉ 03 ENVIOS) COBRANÇA ATIVA ELETRÔNICA',
    89: 'TARIFA MENSAL EMAIL COBRANÇA ATIVA ELETRÔNICA',
    90: 'TARIFA MENSAL SMS COBRANÇA ATIVA ELETRÔNICA',
    91: 'TARIFA MENSAL DE EXCLUSÃO DE ENTRADA DE NEGATIVAÇÃO EXPRESSA',
    92: 'TARIFA MENSAL DE CANCELAMENTO DE NEGATIVAÇÃO EXPRESSA',
    93: 'TARIFA MENSAL DE EXCLUSÃO DE NEGATIVAÇÃO EXPRESSA POR LIQUIDAÇÃO',
}

STR_EVENTO_FORMAT = "%d%m%y"


class L10nBrHrCnab(models.Model):
    _name = "l10n_br.cnab"
    _rec_name = "display_name"

    display_name = fields.Char(
        compute='_compute_display_name',
        store=True,
        index=True
    )

    arquivo_retorno = fields.Binary(
        string='Arquivo Retorno'
    )
    filename = fields.Char(
        string="Filename"
    )
    bank_account_id = fields.Many2one(
        string="Conta cedente",
        comodel_name="res.partner.bank",
    )
    data = fields.Date(
        string="Data CNAB",
        required=True,
        default=datetime.now()
    )
    data_arquivo = fields.Date(
        string="Data Criação no Banco",
    )
    sequencial_arquivo = fields.Char(
        string="Sequencial do Arquivo",
    )
    motivo_erro = fields.Char(
        string="Motivo do Erro",
    )
    lote_id = fields.One2many(
        string="Lotes",
        comodel_name="l10n_br.cnab.lote",
        inverse_name="cnab_id"
    )
    name = fields.Char(
        string="Name",
    )
    num_eventos = fields.Integer(
        string=u"Número de Eventos",
    )
    num_lotes = fields.Integer(
        string=u"Número de Lotes",
    )
    state = fields.Selection(
        string=u"Estágio",
        selection=STATE,
        default="draft",
    )

    @api.one
    @api.depends('name')
    def _compute_display_name(self):
        self.display_name = self.name

    def _busca_conta(self, banco, agencia, conta):
        return self.env['res.partner.bank'].search([
            # ('acc_number', '=', str(banco)),
            ('bra_number', '=', str(agencia)),
            ('acc_number', '=', str(conta))
        ]).id

    def _cria_lote(self, header, lote, evento, trailer):

        if lote.header:
            lote_bank_account_id = self._busca_conta(
                lote.header.codigo_do_banco,
                lote.header.cedente_agencia,
                lote.header.cedente_conta,
            ).id
        else:
            lote_bank_account_id = self.bank_account_id

        vals = {
            'account_bank_id': lote_bank_account_id.id,
            'servico_operacao': header.literal_retorno,
            'tipo_servico': header.literal_servico,
            'qtd_registros': trailer.totais_quantidade_registros,
            'total_valores': float(trailer.valor_total_titulos) / 100,
            'cnab_id': self.id,
        }

        lote_id = self.env['l10n_br.cnab.lote'].create(vals)

        return lote_id, lote_bank_account_id

    def _lote_400(self, evento, lote_id):

        bank_payment_line_id = self.env['bank.payment.line'].search([(
            'nosso_numero', '=', evento.nosso_numero
        )], limit=1)

        vals_evento = {
            'bank_payment_line_id': bank_payment_line_id.id,
            'data_ocorrencia':
                datetime.strptime(
                    str(evento.data_ocorrencia).zfill(6), STR_EVENTO_FORMAT)
                if evento.data_ocorrencia else '',
            'data_real_pagamento':
                datetime.strptime(
                    str(evento.data_credito).zfill(6), STR_EVENTO_FORMAT)
                if evento.data_credito else '',
            'identificacao_titulo_empresa':
                evento.identificacao_titulo_empresa,
            'invoice_id': bank_payment_line_id.
                              payment_line_ids[:1].move_line_id.invoice_id.id,
            'juros_mora_multa': float(evento.juros_mora_multa) / 100,
            'lote_id': lote_id.id,
            'nosso_numero': str(evento.nosso_numero),
            'ocorrencias':
                CODIGO_OCORRENCIAS_CNAB200[evento.codigo_ocorrencia],
            'outros_creditos': float(evento.outros_creditos) / 100,
            'partner_id': bank_payment_line_id.partner_id.id,
            'seu_numero': evento.numero_documento,
            'str_motiv_a':
                COD_REGISTROS_REJEITADOS_CNAB400.get(int(evento.erros[0:2]))
                if evento.erros[0:2] else '',
            'str_motiv_b':
                COD_REGISTROS_REJEITADOS_CNAB400.get(int(evento.erros[2:4]))
                if evento.erros[2:4] else '',
            'str_motiv_c':
                COD_REGISTROS_REJEITADOS_CNAB400.get(int(evento.erros[4:6]))
                if evento.erros[4:6] else '',
            'str_motiv_d':
                COD_REGISTROS_REJEITADOS_CNAB400.get(int(evento.erros[6:8]))
                if evento.erros[6:8] else '',
            'tarifa_cobranca': float(evento.tarifa_cobranca),
            'valor': float(evento.valor) / 100,
            'valor_abatimento': float(evento.valor_abatimento) / 100,
            'valor_desconto': float(evento.valor_desconto) / 100,
            'valor_iof': float(evento.valor_iof) / 100,
            'valor_pagamento': evento.valor_principal,
        }
        cnab_event_id = self.env['l10n_br.cnab.evento'].create(vals_evento)

        amount = 0.0
        line_values = []
        invoices = []
        codigo_ocorrencia = evento.codigo_ocorrencia
        if codigo_ocorrencia and bank_payment_line_id:
            cnab_state = False
            bank_state = False
            if codigo_ocorrencia in RETORNO_400_CONFIRMADA:
                cnab_state = 'accepted'
                bank_state = 'aberta'
            elif codigo_ocorrencia in RETORNO_400_REJEITADA:
                cnab_state = 'not_accepted'
                bank_state = 'inicial'
            elif codigo_ocorrencia in RETORNO_400_LIQUIDACAO:
                cnab_state = 'accepted'
                bank_state = 'liquidada'
            elif codigo_ocorrencia in RETORNO_400_BAIXA:
                cnab_state = 'accepted'
                if codigo_ocorrencia == 9:
                    bank_state = 'baixa'
                else:
                    bank_state = 'baixa_liquidacao'
            else:
                cnab_event_id.str_motiv_e = str(codigo_ocorrencia) + \
                                            ': Ocorrência não tratada'

            if cnab_state:

                for pay_order_line_id in bank_payment_line_id.payment_line_ids:
                    pay_order_line_id.move_line_id.state_cnab = cnab_state
                    pay_order_line_id.move_line_id.nosso_numero = str(
                        evento.nosso_numero
                    )
                    move_line = pay_order_line_id.move_line_id
                    invoice = move_line.invoice_id
                    if bank_state == 'liquidada' and invoice.state == 'open':
                        line_dict = {
                            'name': evento.nosso_numero,
                            'nosso_numero': evento.nosso_numero,
                            'numero_documento': evento.numero_documento,
                            'identificacao_titulo_empresa':
                                evento.identificacao_titulo_empresa,
                            'credit': float(evento.valor_principal) +
                                      float(evento.tarifa_cobranca),
                            'account_id': invoice.payment_mode_id.
                                              default_account_id.id or
                                          invoice.account_id.id,
                            'journal_id':
                                bank_payment_line_id.order_id.\
                                journal_id.id,
                            'date_maturity':
                                datetime.strptime(
                                    str(evento.vencimento).zfill(6),
                                    STR_EVENTO_FORMAT)
                                if evento.vencimento else '',
                            'date':
                                datetime.strptime(
                                    str(evento.data_ocorrencia).zfill(6),
                                    STR_EVENTO_FORMAT)
                                if evento.data_ocorrencia else '',
                            'partner_id': bank_payment_line_id.\
                                partner_id.id
                         }

                        line_values.append((0, 0, line_dict))
                        amount += float(evento.valor_principal)
                        invoices.append(invoice)

                        invoice_line_tax_id = \
                            invoice.invoice_line_ids.filtered(
                                lambda i: i.price_subtotal == float(
                                    evento.tarifa_cobranca))
                        if invoice_line_tax_id:
                            # amount += float(evento.tarifa_cobranca)

                            line_dict_tarifa = dict(line_dict)
                            line_dict_tarifa.update({
                                'name': str(evento.nosso_numero) + ' - Tarifa',
                                'credit': 0,
                                'debit': float(evento.tarifa_cobranca),
                                'account_id': invoice.payment_mode_id.
                                                  default_tax_account_id.id or
                                              invoice.account_id.id,
                            })
                            line_values.append((0, 0, line_dict_tarifa))

                        # TODO: Juros / iof / Desconto / Abatimento /
                        #  Outros Créditos
                        # if evento.juros_mora_multa:
                        #     amount += float(evento.juros_mora_multa)
                        #     line_dict_multa = dict(line_dict)
                        #     line_dict_multa.update({
                        #         'name': str(evento.nosso_numero) + ' - Juros',
                        #         'credit': float(evento.juros_mora_multa),
                        #         'account_id': invoice.account_id.id,
                        #     })
                        #     line_values.append((0, 0, line_dict_multa))

                    if bank_state:
                        move_line.situacao_pagamento = bank_state
                    if cnab_state:
                        move_line.state_cnab = cnab_state

        return line_values, amount, invoices

    def _lote_240(self, evento, lote_id):
        data_evento = str(
            evento.credito_data_real)
        data_evento = fields.Date.from_string(
            data_evento[4:] + "-" + data_evento[2:4] + "-" +
            data_evento[0:2]
        )
        lote_bank_account_id = self.env['res.partner.bank'].search(
            [
                ('bra_number', '=', evento.favorecido_agencia),
                ('bra_number_dig', '=', evento.favorecido_agencia_dv),
                ('acc_number', '=', evento.favorecido_conta),
                ('acc_number_dig', '=', evento.favorecido_conta_dv)
            ])
        lote_bank_account_id = lote_bank_account_id.ids[0] \
            if lote_bank_account_id else False
        favorecido_partner = self.env['res.partner.bank'].search(
            [('owner_name', 'ilike', evento.favorecido_nome)]
        )
        favorecido_partner = favorecido_partner[0].partner_id.id \
            if favorecido_partner else False
        bank_payment_line_id = self.env['bank.payment.line'].search(
            [
                ('name', '=', evento.credito_seu_numero)
            ]
        )
        ocorrencias_dic = dict(CODIGO_OCORRENCIAS)
        ocorrencias = [
            evento.ocorrencias[0:2],
            evento.ocorrencias[2:4],
            evento.ocorrencias[4:6],
            evento.ocorrencias[6:8],
            evento.ocorrencias[8:10]
        ]
        vals_evento = {
            'data_real_pagamento': data_evento,
            'segmento': evento.servico_segmento,
            'favorecido_nome': favorecido_partner,
            'favorecido_conta_bancaria': lote_bank_account_id,
            'nosso_numero': str(evento.credito_nosso_numero),
            'seu_numero': evento.credito_seu_numero,
            'tipo_moeda': evento.credito_moeda_tipo,
            'valor_pagamento': evento.credito_valor_pagamento,
            'ocorrencias': evento.ocorrencias,
            'str_motiv_a': ocorrencias_dic[ocorrencias[0]] if
            ocorrencias[0] else '',
            'str_motiv_b': ocorrencias_dic[ocorrencias[1]] if
            ocorrencias[1] else '',
            'str_motiv_c': ocorrencias_dic[ocorrencias[2]] if
            ocorrencias[2] else '',
            'str_motiv_d': ocorrencias_dic[ocorrencias[3]] if
            ocorrencias[3] else '',
            'str_motiv_e': ocorrencias_dic[ocorrencias[4]] if
            ocorrencias[4] else '',
            'lote_id': lote_id.id,
            'bank_payment_line_id': bank_payment_line_id.id,
        }
        self.env['l10n_br.cnab.evento'].create(vals_evento)
        if evento.ocorrencias and bank_payment_line_id:
            if '00' in ocorrencias:
                bank_state = 'paid'
                cnab_state = 'accepted'

            else:
                bank_state = 'exception'
                cnab_state = 'not_accepted'

            bank_payment_line_id.state2 = bank_state
            for payment_line in bank_payment_line_id.payment_line_ids:
                payment_line.move_line_id.state_cnab = cnab_state

    def _reprocessa_lote_240(self, evento, lote_id):
        raise NotImplementedError("FALTA FAZER")

    def _reprocessa_lote_400(self, evento, lote_id):
        bank_payment_line_id = self.env['bank.payment.line'].search([(
            'identificacao_titulo_empresa', '=',
            evento.identificacao_titulo_empresa
        )], limit=1)

        cnab_event_id = self.env['l10n_br.cnab.evento'].search([
            ('lote_id', '=', lote_id.id),
            ('bank_payment_line_id', '!=', False),
            ('bank_payment_line_id', '=', bank_payment_line_id.id),
        ])

        vals_evento = {
            'bank_payment_line_id':
                cnab_event_id.bank_payment_line_id.id or
                bank_payment_line_id.id,
            'data_ocorrencia':
                datetime.strptime(
                    str(evento.data_ocorrencia).zfill(6), STR_EVENTO_FORMAT)
                if evento.data_ocorrencia else '',
            'data_real_pagamento':
                datetime.strptime(
                    str(evento.data_credito).zfill(6), STR_EVENTO_FORMAT)
                if evento.data_credito else '',
            'identificacao_titulo_empresa':
                evento.identificacao_titulo_empresa,
            'invoice_id': cnab_event_id.invoice_id.id or
                          bank_payment_line_id.payment_line_ids[:1].
                              move_line_id.invoice_id.id,
            'juros_mora_multa': cnab_event_id.juros_mora_multa or
                                float(evento.juros_mora_multa) / 100,
            'lote_id': cnab_event_id.lote_id.id or lote_id.id,
            'nosso_numero': str(evento.nosso_numero),
            'ocorrencias':
                CODIGO_OCORRENCIAS_CNAB200[evento.codigo_ocorrencia],
            'outros_creditos': cnab_event_id.outros_creditos or
                               float(evento.outros_creditos) / 100,
            'partner_id': bank_payment_line_id.partner_id.id,
            'seu_numero': evento.numero_documento,
            'str_motiv_a':
                COD_REGISTROS_REJEITADOS_CNAB400.get(int(evento.erros[0:2]))
                if evento.erros[0:2] else '',
            'str_motiv_b':
                COD_REGISTROS_REJEITADOS_CNAB400.get(int(evento.erros[2:4]))
                if evento.erros[2:4] else '',
            'str_motiv_c':
                COD_REGISTROS_REJEITADOS_CNAB400.get(int(evento.erros[4:6]))
                if evento.erros[4:6] else '',
            'str_motiv_d':
                COD_REGISTROS_REJEITADOS_CNAB400.get(int(evento.erros[6:8]))
                if evento.erros[6:8] else '',
            'tarifa_cobranca': cnab_event_id.tarifa_cobranca or
                               float(evento.tarifa_cobranca),
            'valor': cnab_event_id.valor or float(evento.valor) / 100,
            'valor_abatimento': cnab_event_id.valor_abatimento or
                                float(evento.valor_abatimento) / 100,
            'valor_desconto': cnab_event_id.valor_desconto or
                              float(evento.valor_desconto) / 100,
            'valor_iof': cnab_event_id.valor_iof or
                         float(evento.valor_iof) / 100,
            'valor_pagamento': cnab_event_id.valor_pagamento or
                               evento.valor_principal,
        }

        if not cnab_event_id:
            cnab_event_id = cnab_event_id.create(vals_evento)
        else:
            cnab_event_id.write(vals_evento)

        amount = 0.0
        codigo_ocorrencia = evento.codigo_ocorrencia
        if codigo_ocorrencia and bank_payment_line_id:

            if not any(codigo_ocorrencia in x for x in RETORNOS_TRATADOS):
                cnab_event_id.str_motiv_e = str(codigo_ocorrencia) + \
                                                ': Ocorrência não tratada'

            bank_payment_line_id.nosso_numero = str(evento.nosso_numero)
            for pay_order_line_id in bank_payment_line_id.payment_line_ids:
                pay_order_line_id.move_line_id.nosso_numero = str(
                    evento.nosso_numero
                )
                pay_order_line_id.nosso_numero = str(evento.nosso_numero)
                debit_move_line = pay_order_line_id.move_line_id
                credit_move_line = self.env['account.move.line'].search([
                    '|',
                    ('nosso_numero', '=', evento.nosso_numero),
                    ('name', '=', evento.nosso_numero),
                    ('credit', '>', 0),
                ])

                if not credit_move_line and debit_move_line.full_reconcile_id:
                    credit_move_line = \
                        debit_move_line.full_reconcile_id.\
                            reconciled_line_ids - debit_move_line

                if not credit_move_line:
                    return
                    # raise UserError(
                    #     "Não foi encontrada uma linha correspondente para a "
                    #     "linha de nosso_numero: %s" % evento.nosso_numero)

                line_values = {
                    'name': evento.nosso_numero,
                    'nosso_numero': evento.nosso_numero,
                    'numero_documento': evento.numero_documento,
                    'identificacao_titulo_empresa':
                        evento.identificacao_titulo_empresa,
                    'date_maturity':
                        datetime.strptime(
                            str(evento.vencimento).zfill(6),
                            STR_EVENTO_FORMAT)
                        if evento.vencimento else '',
                    'date':
                        datetime.strptime(
                            str(evento.data_ocorrencia).zfill(6),
                            STR_EVENTO_FORMAT)
                        if evento.data_ocorrencia else '',
                }

                credit_move_line.with_context(
                    reprocessing=True).write(line_values)

    @api.model
    def reprocessar_retorno_multi(self):
        active_ids = self._context.get("active_ids")

        for cnab_id in self.browse(active_ids):
            if cnab_id.state in ['done']:
                cnab_id.reprocessar_arquivo_retorno()

    @api.multi
    def reprocessar_arquivo_retorno(self):
        cnab_type, arquivo_parser = Cnab.detectar_retorno(self.arquivo_retorno)
        data_arquivo = str(arquivo_parser.header.arquivo_data_de_geracao)
        self.sequencial_arquivo = str(arquivo_parser.header.sequencial_arquivo)
        self.data_arquivo = datetime.strptime(data_arquivo, "%d%m%y")

        self.bank_account_id = self._busca_conta(
            arquivo_parser.header.codigo_do_banco,
            arquivo_parser.header.cedente_agencia,
            arquivo_parser.header.cedente_conta,
        )

        self.num_lotes = len(arquivo_parser.lotes)
        self.num_eventos = arquivo_parser.trailer.totais_quantidade_registros
        for lote in arquivo_parser.lotes:

            header = lote.header or arquivo_parser.header
            trailer = lote.trailer or arquivo_parser.trailer

            lote_id = self.lote_id and self.lote_id[0]
            bankless_line_id = \
                lote_id.evento_id.filtered(
                    lambda e: not e.bank_payment_line_id)
            bankless_line_id.unlink()

            for evento in lote.eventos:
                if not lote_id:
                    lote_id, lote_bank_account_id = self._cria_lote(
                        header, lote, evento, trailer)

                if cnab_type == '240':
                    self._reprocessa_lote_240(evento, lote_id)
                else:
                    self._reprocessa_lote_400(evento, lote_id)

            #TODO: Verificar necessidade de atualizar dados do Account.Move
            return self.write({'state': 'done'})

    @api.multi
    def processar_arquivo_retorno(self):
        cnab_type, arquivo_parser = Cnab.detectar_retorno(self.arquivo_retorno)
        # if not arquivo_parser.header.arquivo_codigo == u'2':
        #     raise exceptions.Warning(
        #         u"Este não é um arquivo de retorno!"
        #     )
        data_arquivo = str(arquivo_parser.header.arquivo_data_de_geracao)
        self.sequencial_arquivo = str(arquivo_parser.header.sequencial_arquivo)
        self.data_arquivo = datetime.strptime(data_arquivo, "%d%m%y")

        if self.search([
            ('data_arquivo', '=', self.data_arquivo),
            ('sequencial_arquivo', '=', self.sequencial_arquivo),
            ('id', '!=', self.id)]):
            self.state = 'error'
            self.motivo_erro = u"O arquivo %s, de %s - sequencial %s, " \
                               u"ja se encontra importado." % \
                               (self.filename,
                                datetime.strftime(fields.Datetime.from_string(
                                    self.data_arquivo), "%d/%m/%Y"),
                                self.sequencial_arquivo)
            return

        self.bank_account_id = self._busca_conta(
            arquivo_parser.header.codigo_do_banco,
            arquivo_parser.header.cedente_agencia,
            arquivo_parser.header.cedente_conta,
        )

        self.num_lotes = len(arquivo_parser.lotes)
        self.num_eventos = arquivo_parser.trailer.totais_quantidade_registros
        for lote in arquivo_parser.lotes:

            header = lote.header or arquivo_parser.header
            trailer = lote.trailer or arquivo_parser.trailer

            lote_id = False
            total_amount = 0.0
            lines = []
            inv_list = []
            for evento in lote.eventos:
                if not lote_id:
                    lote_id, lote_bank_account_id = self._cria_lote(
                        header, lote, evento, trailer)

                if cnab_type == '240':
                    self._lote_240(evento, lote_id)
                else:
                    line_vals, line_amount, invoices = \
                        self._lote_400(evento, lote_id)
                    for inv in invoices:
                        inv_list.append(inv)
                    if line_vals and line_amount:
                        for line in line_vals:
                            lines.append(line)
                        total_amount += line_amount

            if total_amount and lines:
                counterpart_account_id = self.env['account.journal'].browse(
                    lines[0][2]['journal_id']).default_debit_account_id.id

                lines.append(
                    (0, 0, {
                        'name': 'cobranca',
                        'debit': total_amount,
                        'account_id': counterpart_account_id,
                        'journal_id': lines[0][2]['journal_id'],
                        'date_maturity': False,
                        'partner_id': False,
                    })
                )
                move = self.env['account.move'].create({
                    'name': 'RetornoCnab_' + fields.Datetime.now(),
                    'ref':
                        'Retorno Gerado em %s' %
                        datetime.strftime(datetime.strptime(
                            data_arquivo, "%d%m%y"), "%d/%m/%Y"),
                    'date': str(datetime.now()),
                    'line_ids': lines,
                    'journal_id': lines[0][2]['journal_id']
                })
                move.post()

                for inv in inv_list:
                    if inv.state != 'open':
                        continue
                    inv_move_lines = inv.move_line_receivable_id
                    pay_move_lines = move.line_ids.filtered(
                        lambda x: x.account_id == inv_move_lines.account_id and
                        x.partner_id == inv_move_lines.partner_id and
                        x.name == inv_move_lines.transaction_ref
                    )
                    move_lines = pay_move_lines | inv_move_lines
                    move_lines.reconcile()

        return self.write({'state': 'done'})

    def _get_name(self, data, filename):
        cnab_ids = self.search([('data', '=', data)], order='id desc')
        cnab_idx = 1
        if cnab_ids:
            search_result = \
                filter(lambda x: x is not None,
                       [re.search(r'\((\d)\)', name) for name in self.search(
                           [('data', '=', data), ('id', '!=', self.id)],
                           order='id desc'
                       ).mapped('name')])
            if search_result:
                cnab_idx = max(int(result.group(1))
                               for result in search_result) + 1

        cnab_name = "{}({}){}".format(
            data, cnab_idx, ' - ' + filename if filename else '')
        return cnab_name

    @api.multi
    def write(self, vals):
        if any(v in vals for v in ['data', 'filename']):
            data = vals.get('data') or self.data
            filename = vals.get('filename') or self.filename

            name = self._get_name(data, filename)
            vals.update({'name': name})
        return super(L10nBrHrCnab, self).write(vals)

    @api.model
    def create(self, vals):
        name = self._get_name(vals.get('data'), vals.get('filename'))
        vals.update({'name': name})
        return super(L10nBrHrCnab, self).create(vals)
