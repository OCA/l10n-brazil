# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from __future__ import division, print_function, unicode_literals

FINAN_DIVIDA = [
    ('a_receber', 'Contas a receber'),
    ('a_pagar', 'Contas a pagar'),
]
FINAN_DIVIDA_A_RECEBER= 'a_receber'
FINAN_DIVIDA_A_PAGAR = 'a_pagar'

FINAN_ENTRADA_SAIDA_CAIXA = [
    ('recebimento', 'Recebimentos'),
    ('pagamento', 'Pagamentos'),
    ('entrada', 'Entradas'),
    ('saida', 'Saídas'),
]
FINAN_RECEBIMENTO = 'recebimento'
FINAN_PAGAMENTO = 'pagamento'
FINAN_ENTRADA = 'entrada'
FINAN_SAIDA = 'saida'

FINAN_LANCAMENTO_ENTRADA = [
    FINAN_RECEBIMENTO,
    FINAN_ENTRADA,
]
FINAN_LANCAMENTO_SAIDA = [
    FINAN_PAGAMENTO,
    FINAN_SAIDA,
]

FINAN_TIPO = FINAN_DIVIDA + FINAN_ENTRADA_SAIDA_CAIXA
FINAN_TIPO_DIVIDA = [FINAN_DIVIDA_A_RECEBER, FINAN_DIVIDA_A_PAGAR]
FINAN_TIPO_PAGAMENTO = [FINAN_RECEBIMENTO, FINAN_PAGAMENTO]
FINAN_TIPO_ENTRADA = [FINAN_DIVIDA_A_RECEBER, FINAN_RECEBIMENTO, FINAN_ENTRADA]
FINAN_TIPO_SAIDA = [FINAN_DIVIDA_A_PAGAR, FINAN_PAGAMENTO, FINAN_SAIDA]
FINAN_TIPO_DICT = dict(FINAN_TIPO)

FINAN_TIPO_CODIGO = {
    FINAN_DIVIDA_A_RECEBER: 'CR',
    FINAN_DIVIDA_A_PAGAR: 'CP',
    FINAN_RECEBIMENTO: 'RR',
    FINAN_PAGAMENTO: 'PP',
    FINAN_ENTRADA: 'TE',
    FINAN_SAIDA: 'TS',
}

FINAN_STATE = [
    ('draft', 'Provisório'),
    ('open', 'Efetivo'),
    ('paid', 'Quitado'),
    ('cancelled', 'Baixado'),
]
FINAN_STATE_DRAFT = 'draft'
FINAN_STATE_OPEN = 'open'
FINAN_STATE_PAID = 'paid'
FINAN_STATE_CANCELLED = 'cancelled'

FINAN_SITUACAO_DIVIDA = [
    ('a_vencer', 'A vencer'),
    ('vence_hoje', 'Vence hoje'),
    ('vencido', 'Vencido'),
    ('quitado', 'Quitado'),
    ('quitado_parcialmente', 'Quitado parcialmente'),
    ('baixado', 'Baixado'),
    ('baixado_parcialmente', 'Baixado parcialmente'),
]

FINAN_SITUACAO_DIVIDA_A_VENCER = 'a_vencer'
FINAN_SITUACAO_DIVIDA_VENCE_HOJE = 'vence_hoje'
FINAN_SITUACAO_DIVIDA_VENCIDO = 'vencido'
FINAN_SITUACAO_DIVIDA_QUITADO = 'quitado'
FINAN_SITUACAO_DIVIDA_QUITADO_PARCIALMENTE = 'quitado_parcialmente'
FINAN_SITUACAO_DIVIDA_BAIXADO = 'baixado'
FINAN_SITUACAO_DIVIDA_BAIXADO_PARCIALMENTE = 'baixado_parcialmente'

FINAN_SITUACAO_DIVIDA_CONSIDERA_ABERTO = [
    FINAN_SITUACAO_DIVIDA_A_VENCER,
    FINAN_SITUACAO_DIVIDA_VENCE_HOJE,
    FINAN_SITUACAO_DIVIDA_VENCIDO,
    FINAN_SITUACAO_DIVIDA_QUITADO_PARCIALMENTE,
]

FINAN_SITUACAO_DIVIDA_CONSIDERA_QUITADO = [
    FINAN_SITUACAO_DIVIDA_QUITADO,
    FINAN_SITUACAO_DIVIDA_QUITADO_PARCIALMENTE,
    FINAN_SITUACAO_DIVIDA_BAIXADO_PARCIALMENTE,
]

FINAN_SITUACAO_DIVIDA_CONSIDERA_BAIXADO = [
    FINAN_SITUACAO_DIVIDA_BAIXADO,
    FINAN_SITUACAO_DIVIDA_BAIXADO_PARCIALMENTE,
]

FINAN_SITUACAO_DIVIDA_SIMPLES = [
    ('aberto', 'Aberto'),
    ('quitado', 'Quitado'),
    ('baixado', 'Baixado'),
]
FINAN_SITUACAO_DIVIDA_SIMPLES_DICT = dict(FINAN_SITUACAO_DIVIDA_SIMPLES)

FINAN_SITUACAO_DIVIDA_SIMPLES_ABERTO = 'aberto'
FINAN_SITUACAO_DIVIDA_SIMPLES_QUITADO = 'quitado'
FINAN_SITUACAO_DIVIDA_SIMPLES_BAIXADO = 'baixado'

FINAN_SEQUENCE = {
    'a_receber': 'financial.move.receivable',
    'recebimento': 'financial.move.receipt',
    'a_pagar': 'financial.move.payable',
    'pagamento': 'financial.move.payment',
}


FINAN_LANCAMENTO_CAMPO = (
    ('vr_documento', 'Valor do documento'),
    ('vr_juros', 'Valor de juros'),
    ('vr_multa', 'Valor de multa'),
    ('vr_outros_creditos', 'Outros créditos'),
    ('vr_desconto', 'Valor de desconto'),
    ('vr_outros_debitos', 'Outros débitos'),
    ('vr_tarifas', 'Tarifas'),
    ('vr_adiantado', 'Valor adiantado'),
    ('vr_baixado', 'Valor baixado'),
    ('vr_total', 'Valor total'),
    ('vr_quitado', 'Valor quitado'),
    ('vr_saldo', 'Saldo em aberto'),
)

FINAN_CONTRATO_STATE = (
    ('draft', 'Provisório'),
    ('confirmed', 'Efetido'),
    ('cancelled', 'Cancelado'),
)
FINAN_CONTRATO_STATE_DRAFT = 'draft'
FINAN_CONTRATO_STATE_CONFIRMED = 'confirmed'
FINAN_CONTRATO_STATE_CANCELLED = 'cancelled'


FINAN_BANCO_CHEQUE_BOLETO = [
    ['001', '001 - Brasil'],
    ['033', '033 - Santander'],
    ['085', '085 - Viacredi'],
    ['104', '104 - Caixa'],
    ['136', '136 - Unicred'],
    ['237', '237 - Bradesco'],
    ['341', '341 - Itaú'],
    ['748', '748 - Sicredi'],
    ['756', '756 - Sicoob'],
]

FINAN_BANCO = [
    ['000', '000 - Interno'],
] + FINAN_BANCO_CHEQUE_BOLETO
FINAN_BANCO_DICT = dict(FINAN_BANCO)

FINAN_BANCO_INTERNO = '000'
FINAN_BANCO_BRASIL = '001'
FINAN_BANCO_SANTANDER = '033'
FINAN_BANCO_VIACREDI = '085'
FINAN_BANCO_CAIXA = '104'
FINAN_BANCO_UNICRED = '136'
FINAN_BANCO_BRADESCO = '237'
FINAN_BANCO_ITAU = '341'
FINAN_BANCO_SICREDI = '748'
FINAN_BANCO_SICOOB = '756'


FINAN_TIPO_CONTA_BANCARIA = (
    #('adiantamento', 'Adiantamento'),
    ('aplicacao', 'Aplicação'),
    ('caixa', 'Caixa'),
    ('capital', 'Capital'),
    ('cobranca', 'Cobrança'),
    ('corrente', 'Corrente'),
    #('devolucao', 'Devolução'),
    ('poupanca', 'Poupança'),
    ('provisao', 'Provisão'),
)
FINAN_TIPO_CONTA_BANCARIA_DICT = dict(FINAN_TIPO_CONTA_BANCARIA)

FINAN_TIPO_CONTA_BANCARIA_ADIANTAMENTO = 'adiantamento'
FINAN_TIPO_CONTA_BANCARIA_APLICACAO = 'aplicacao'
FINAN_TIPO_CONTA_BANCARIA_CAIXA = 'caixa'
FINAN_TIPO_CONTA_BANCARIA_CAPITAL = 'capital'
FINAN_TIPO_CONTA_BANCARIA_COBRANCA = 'cobranca'
FINAN_TIPO_CONTA_BANCARIA_CORRENTE = 'corrente'
FINAN_TIPO_CONTA_BANCARIA_DEVOLUCAO = 'devolucao'
FINAN_TIPO_CONTA_BANCARIA_POUPANCA = 'poupanca'
FINAN_TIPO_CONTA_BANCARIA_PROVISAO = 'provisao'
