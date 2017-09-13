# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia
#   Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from __future__ import division, print_function, unicode_literals

from odoo import fields, models
from odoo.addons.l10n_br_base.constante_tributaria import (
    MODELO_FISCAL,
    MODELO_FISCAL_NFE,
    TIPO_EMISSAO,
    TIPO_EMISSAO_PROPRIA,
    ENTRADA_SAIDA,
    ENTRADA_SAIDA_SAIDA,
    REGIME_TRIBUTARIO,
    REGIME_TRIBUTARIO_SIMPLES,
    IND_FORMA_PAGAMENTO,
    IND_FORMA_PAGAMENTO_A_VISTA,
    FINALIDADE_NFE,
    FINALIDADE_NFE_NORMAL,
    MODALIDADE_FRETE,
    LIMITE_RETENCAO_PIS_COFINS_CSLL,
    NATUREZA_TRIBUTACAO_NFSE,
    TIPO_CONSUMIDOR_FINAL,
    TIPO_CONSUMIDOR_FINAL_NORMAL,
    INDICADOR_PRESENCA_COMPRADOR,
    INDICADOR_PRESENCA_COMPRADOR_NAO_SE_APLICA,
    ST_ISS,
    MODALIDADE_FRETE_DESTINATARIO_PROPRIO,
)


class SpedOperacaoFiscal(models.Model):
    _name = b'sped.operacao'
    _description = 'Operações Fiscais'
    _order = 'emissao, modelo, nome'
    _rec_name = 'nome'

    empresa_id = fields.Many2one(
        comodel_name='sped.empresa',
        string='Empresa',
        ondelete='restrict'
    )
    modelo = fields.Selection(
        selection=MODELO_FISCAL,
        string='Modelo',
        required=True,
        index=True,
        default=MODELO_FISCAL_NFE
    )
    emissao = fields.Selection(
        selection=TIPO_EMISSAO,
        string='Tipo de emissão',
        index=True,
        default=TIPO_EMISSAO_PROPRIA
    )
    entrada_saida = fields.Selection(
        selection=ENTRADA_SAIDA,
        string='Entrada/saída',
        index=True,
        default=ENTRADA_SAIDA_SAIDA
    )
    nome = fields.Char(
        string='Nome',
        size=120,
        index=True
    )
    codigo = fields.Char(
        string='Código',
        size=60,
        index=True
    )
    serie = fields.Char(
        string='Série',
        size=3
    )
    regime_tributario = fields.Selection(
        selection=REGIME_TRIBUTARIO,
        string='Regime tributário',
        default=REGIME_TRIBUTARIO_SIMPLES
    )
    ind_forma_pagamento = fields.Selection(
        selection=IND_FORMA_PAGAMENTO,
        string='Tipo de pagamento',
        default=IND_FORMA_PAGAMENTO_A_VISTA
    )
    finalidade_nfe = fields.Selection(
        selection=FINALIDADE_NFE,
        string='Finalidade da NF-e',
        default=FINALIDADE_NFE_NORMAL
    )
    modalidade_frete = fields.Selection(
        selection=MODALIDADE_FRETE,
        string='Modalidade do frete',
        default=MODALIDADE_FRETE_DESTINATARIO_PROPRIO
    )
    natureza_operacao_id = fields.Many2one(
        comodel_name='sped.natureza.operacao',
        string='Natureza da operação',
        ondelete='restrict'
    )
    infadfisco = fields.Text(
        string='Informações adicionais de interesse do fisco'
    )
    infcomplementar = fields.Text(
        string='Informações complementares'
    )
    #
    # Retenção de impostos
    #
    deduz_retencao = fields.Boolean(
        string='Deduz retenção do total da NF?',
        default=True
    )
    pis_cofins_retido = fields.Boolean(
        string='PIS-COFINS retidos?'
    )
    al_pis_retido = fields.Float(
        string='Alíquota do PIS',
        default=0.65,
        digits=(5, 2)
    )
    al_cofins_retido = fields.Float(
        string='Alíquota da COFINS',
        default=3,
        digits=(5, 2)
    )
    csll_retido = fields.Boolean(
        string='CSLL retido?'
    )
    al_csll = fields.Float(
        string='Alíquota da CSLL',
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
        string='Moeda',
        default=lambda self: self.env.ref('base.BRL').id
    )
    limite_retencao_pis_cofins_csll = fields.Monetary(
        string='Obedecer limite de faturamento para retenção de',
        default=LIMITE_RETENCAO_PIS_COFINS_CSLL
    )
    irrf_retido = fields.Boolean(
        string='IR retido?'
    )
    irrf_retido_ignora_limite = fields.Boolean(
        string='IR retido ignora limite de R$ 10,00?',
    )
    al_irrf = fields.Float(
        string='Alíquota do IR',
        default=1,
        digits=(5, 2),
    )
    #
    # Notas de serviço
    #
    inss_retido = fields.Boolean(
        string='INSS retido?',
    )
    cnae_id = fields.Many2one(
        comodel_name='sped.cnae',
        string='CNAE'
    )
    natureza_tributacao_nfse = fields.Selection(
        selection=NATUREZA_TRIBUTACAO_NFSE,
        string='Natureza da tributação',
    )
    servico_id = fields.Many2one(
        comodel_name='sped.servico',
        string='Serviço'
    )
    cst_iss = fields.Selection(
        selection=ST_ISS,
        string='CST ISS'
    )
    # 'forca_recalculo_st_compra': fields.boolean(
    # 'Força recálculo do ST na compra?'),
    # 'operacao_entrada_id': fields.many2one(
    # 'sped.operacao', 'Operação de entrada equivalente'),
    consumidor_final = fields.Selection(
        selection=TIPO_CONSUMIDOR_FINAL,
        string='Tipo do consumidor',
        default=TIPO_CONSUMIDOR_FINAL_NORMAL
    )
    presenca_comprador = fields.Selection(
        selection=INDICADOR_PRESENCA_COMPRADOR,
        string='Presença do comprador',
        default=INDICADOR_PRESENCA_COMPRADOR_NAO_SE_APLICA
    )
    preco_automatico = fields.Selection(
        selection=[
            ('V', 'Venda'),
            ('C', 'Custo'),
            ('T', 'Transferência'),
        ],
        string='Traz preço automático?',
    )

    # def calcula_imposto(self):
    #     self.ensure_one()
    #
    #     calculo = self.env['sped.calculo.imposto.item'].new()
    #     calculo.operacao_id = self.id
    #     # calculo.empresa_id = empresa_id
    #     # calculo.participante_id = participante_id
    #     # calculo.produto_id = produto_id
    #     # calculo.quantidade = quantidade
    #     # calculo.vr_unitario = vr_unitario
    #
    #     calculo.empresa_id = 1
    #     calculo.participante_id = 1
    #     calculo.produto_id = 1
    #     calculo.quantidade = 10
    #     calculo.vr_unitario = 100
    #     calculo.data_emissao = fields.Date.today()
    #     calculo.calcula_impostos()
    #
    #     print(calculo.vr_nf)
