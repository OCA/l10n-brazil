# -*- coding: utf-8 -*-
#
# Copyright 2017 Taŭga Tecnologia
#   Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from __future__ import division, print_function, unicode_literals


NATUREZA_CONTA_CONTABIL = (
    ('01', 'Ativo'),
    ('02', 'Passivo'),
    ('03', 'Patrimônio líquido'),
    ('04', 'Resultado'),
    ('05', 'Compensação'),
    ('09', 'Outras'),
)
NATUREZA_CONTA_CONTABIL_ATIVO = '01'
NATUREZA_CONTA_CONTABIL_PASSIVO = '02'
NATUREZA_CONTA_CONTABIL_PATRIMONIO = '03'
NATUREZA_CONTA_CONTABIL_RESULTADO = '04'
NATUREZA_CONTA_CONTABIL_COMPENSACAO = '05'
NATUREZA_CONTA_CONTABIL_OUTRAS = '09'


TIPO_SPED_CONTA_CONTABIL = (
    ('S', 'Sintética'),
    ('A', 'Analítica'),
)
TIPO_SPED_CONTA_CONTABIL_SINTETICA = 'S'
TIPO_SPED_CONTA_CONTABIL_ANALITICA = 'A'


TIPO_CONTA_CONTABIL = (
    ('ativo', 'Ativo'),  # natureza 01
    ('caixa', 'Caixa e bancos'),  # natureza 01
    ('receber', 'A receber'),  # natureza 01
    ('passivo', 'Passivo'),  # natureza 02
    ('receita', 'Receita'),  # natureza 09
    ('despesa', 'Despesa'),  # natureza 09
    ('custo', 'Custo'),  # natureza 09
    ('pagar', 'A pagar'),  # natureza 02
    ('resultado', 'Resultado'),  # natureza 04
    ('compensacao', 'Compensação'),  # natureza 05
    ('patrimonio', 'Patrimônio líquido'),  # natureza 03
    ('outras', 'Outras'),  # natureza 09
)
TIPO_CONTA_CONTABIL_ATIVO = 'ativo'
TIPO_CONTA_CONTABIL_CAIXA = 'caixa'
TIPO_CONTA_CONTABIL_RECEBER = 'receber'
TIPO_CONTA_CONTABIL_PASSIVO = 'passivo'
TIPO_CONTA_CONTABIL_RECEITA = 'receita'
TIPO_CONTA_CONTABIL_DESPESA = 'despesa'
TIPO_CONTA_CONTABIL_CUSTO = 'custo'
TIPO_CONTA_CONTABIL_PAGAR = 'pagar'
TIPO_CONTA_CONTABIL_RESULTADO = 'resultado'
TIPO_CONTA_CONTABIL_COMPENSACAO = 'compensacao'
TIPO_CONTA_CONTABIL_PATRIMONIO = 'patrimonio'
TIPO_CONTA_CONTABIL_OUTRAS = 'outras'

TIPO_CONTA_CONTABIL_NATUREZA = {
    TIPO_CONTA_CONTABIL_ATIVO: NATUREZA_CONTA_CONTABIL_ATIVO,
    TIPO_CONTA_CONTABIL_CAIXA: NATUREZA_CONTA_CONTABIL_ATIVO,
    TIPO_CONTA_CONTABIL_RECEBER: NATUREZA_CONTA_CONTABIL_ATIVO,
    TIPO_CONTA_CONTABIL_PASSIVO: NATUREZA_CONTA_CONTABIL_PASSIVO,
    TIPO_CONTA_CONTABIL_RECEITA: NATUREZA_CONTA_CONTABIL_OUTRAS,
    TIPO_CONTA_CONTABIL_DESPESA: NATUREZA_CONTA_CONTABIL_OUTRAS,
    TIPO_CONTA_CONTABIL_CUSTO: NATUREZA_CONTA_CONTABIL_OUTRAS,
    TIPO_CONTA_CONTABIL_PAGAR: NATUREZA_CONTA_CONTABIL_PASSIVO,
    TIPO_CONTA_CONTABIL_RESULTADO: NATUREZA_CONTA_CONTABIL_RESULTADO,
    TIPO_CONTA_CONTABIL_COMPENSACAO: NATUREZA_CONTA_CONTABIL_COMPENSACAO,
    TIPO_CONTA_CONTABIL_PATRIMONIO: NATUREZA_CONTA_CONTABIL_PATRIMONIO,
    TIPO_CONTA_CONTABIL_OUTRAS: NATUREZA_CONTA_CONTABIL_OUTRAS,
}


NATUREZA_PARTIDA = (
    ('D', 'Débito'),
    ('C', 'Crédito'),
)
NATUREZA_PARTIDA_DEBITO = 'D'
NATUREZA_PARTIDA_CREDITO = 'C'

CAMPO_DOCUMENTO_FISCAL = [
    ('vr_cofins_proprio', u'COFINS própria'),
    ('vr_cofins_retido', u'COFINS retida'),
    ('vr_icms_sn', u'Crédito de ICMS - SIMPLES Nacional'),
    ('vr_csll_propria', u'CSLL própria'),
    ('vr_csll', u'CSLL retida'),
    ('vr_custo_comercial', u'Custo (nas entradas/compras)'),
    ('vr_custo_estoque', u'Custo médio (nas saídas/vendas)'),
    ('vr_desconto', u'Desconto'),
    ('vr_diferencial_aliquota', u'Diferencial de alíquota (ICMS próprio)'),
    ('vr_diferencial_aliquota_st', u'Diferencial de alíquota (ICMS ST)'),
    ('vr_frete', u'Frete'),
    ('vr_icms_proprio', u'ICMS próprio'),
    ('vr_icms_st', u'ICMS ST'),
    ('vr_ii', u'Imposto de importação'),
    ('vr_previdencia', u'INSS retido'),
    ('vr_ipi', u'IPI'),
    ('vr_irpj_proprio', u'IRPJ próprio'),
    ('vr_irrf', u'IRRF retido'),
    ('vr_iss', u'ISS próprio'),
    ('vr_iss_retido', u'ISS retido'),
    ('vr_outras', u'Outras despesas acessórias'),
    ('vr_pis_proprio', u'PIS próprio'),
    ('vr_pis_retido', u'PIS retido'),
    ('vr_seguro', u'Seguro'),
    ('vr_simples', u'SIMPLES'),
    ('vr_fatura', u'Total da fatura'),
    ('vr_nf', u'Total da NF'),
    ('vr_operacao', u'Valor da operação'),
]

CAMPO_DOCUMENTO_FISCAL_ITEM = (
    'vr_custo_comercial',
    'vr_custo_estoque',
    'vr_icms_proprio',
    'vr_icms_st',
    'vr_ipi',
    'vr_operacao',
)