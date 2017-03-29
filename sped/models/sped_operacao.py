# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia
#   Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#


from odoo import fields, models
from ..constante_tributaria import *


class OperacaoFiscal(models.Model):
    _description = u'Operações Fiscais'
    _name = 'sped.operacao'
    _order = 'emissao, modelo, nome'
    _rec_name = 'nome'

    empresa_id = fields.Many2one(
        comodel_name='sped.empresa',
        string=u'Empresa',
        ondelete='restrict'
    )
    modelo = fields.Selection(
        selection=MODELO_FISCAL,
        string=u'Modelo',
        required=True,
        index=True,
        default=MODELO_FISCAL_NFE
    )
    emissao = fields.Selection(
        selection=TIPO_EMISSAO,
        string=u'Tipo de emissão',
        index=True,
        default=TIPO_EMISSAO_PROPRIA
    )
    entrada_saida = fields.Selection(
        selection=ENTRADA_SAIDA,
        string=u'Entrada/saída',
        index=True,
        default=ENTRADA_SAIDA_SAIDA
    )
    nome = fields.Char(
        string=u'Nome',
        size=120,
        index=True
    )
    codigo = fields.Char(
        string=u'Código',
        size=60,
        index=True
    )
    serie = fields.Char(
        string=u'Série',
        size=3
    )
    regime_tributario = fields.Selection(
        selection=REGIME_TRIBUTARIO,
        string=u'Regime tributário',
        default=REGIME_TRIBUTARIO_SIMPLES
    )
    ind_forma_pagamento = fields.Selection(
        selection=IND_FORMA_PAGAMENTO,
        string=u'Tipo de pagamento',
        default=IND_FORMA_PAGAMENTO_A_VISTA
    )
    finalidade_nfe = fields.Selection(
        selection=FINALIDADE_NFE,
        string=u'Finalidade da NF-e',
        default=FINALIDADE_NFE_NORMAL
    )
    modalidade_frete = fields.Selection(
        selection=MODALIDADE_FRETE,
        string=u'Modalidade do frete',
        default=MODALIDADE_FRETE_DESTINATARIO_PROPRIO
    )
    natureza_operacao_id = fields.Many2one(
        comodel_name='sped.natureza.operacao',
        string=u'Natureza da operação',
        ondelete='restrict'
    )
    infadfisco = fields.Text(
        string=u'Informações adicionais de interesse do fisco'
    )
    infcomplementar = fields.Text(
        string=u'Informações complementares'
    )
    #
    # Retenção de impostos
    #
    deduz_retencao = fields.Boolean(
        string=u'Deduz retenção do total da NF?',
        default=True
    )
    pis_cofins_retido = fields.Boolean(
        string=u'PIS-COFINS retidos?'
    )
    al_pis_retido = fields.Float(
        string=u'Alíquota do PIS',
        default=0.65,
        digits=(5, 2)
    )
    al_cofins_retido = fields.Float(
        string=u'Alíquota da COFINS',
        default=3,
        digits=(5, 2)
    )
    csll_retido = fields.Boolean(
        string=u'CSLL retido?'
    )
    al_csll = fields.Float(
        string=u'Alíquota da CSLL',
        default=1,
        digits=(5, 2)
    )
    #
    # Para todos os valores de referência numa operação fiscal,
    # a moeda é SEMPRE o
    # Real BRL
    #
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string=u'Moeda',
        default=lambda self: self.env.ref('base.BRL').id
    )
    limite_retencao_pis_cofins_csll = fields.Monetary(
        string=u'Obedecer limite de faturamento para retenção de',
        default=LIMITE_RETENCAO_PIS_COFINS_CSLL
    )
    irrf_retido = fields.Boolean(
        string=u'IR retido?'
    )
    irrf_retido_ignora_limite = fields.Boolean(
        string=u'IR retido ignora limite de R$ 10,00?',
    )
    al_irrf = fields.Float(
        string=u'Alíquota do IR',
        default=1,
        digits=(5, 2),
    )
    #
    # Notas de serviço
    #
    inss_retido = fields.Boolean(
        string=u'INSS retido?',
    )
    cnae_id = fields.Many2one(
        comodel_name='sped.cnae',
        string=u'CNAE'
    )
    natureza_tributacao_nfse = fields.Selection(
        selection=NATUREZA_TRIBUTACAO_NFSE,
        string=u'Natureza da tributação',
    )
    servico_id = fields.Many2one(
        comodel_name='sped.servico',
        string=u'Serviço'
    )
    cst_iss = fields.Selection(
        selection=ST_ISS,
        string=u'CST ISS'
    )
    # 'forca_recalculo_st_compra': fields.boolean(
    # 'Força recálculo do ST na compra?'),
    # 'operacao_entrada_id': fields.many2one(
    # 'sped.operacao', 'Operação de entrada equivalente'),
    consumidor_final = fields.Selection(
        selection=TIPO_CONSUMIDOR_FINAL,
        string=u'Tipo do consumidor',
        default=TIPO_CONSUMIDOR_FINAL_NORMAL
    )
    presenca_comprador = fields.Selection(
        selection=INDICADOR_PRESENCA_COMPRADOR,
        string=u'Presença do comprador',
        default=INDICADOR_PRESENCA_COMPRADOR_NAO_SE_APLICA
    )

    preco_automatico = fields.Selection([
        ('V', 'Venda'),
        ('C', 'Custo')
    ],
        string=u'Traz preço automático?',
    )
