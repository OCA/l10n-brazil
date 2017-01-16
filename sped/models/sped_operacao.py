# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia - Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#


from __future__ import division, print_function, unicode_literals

from odoo import fields, models
import odoo.addons.decimal_precision as dp
from ..constante_tributaria import *


class OperacaoFiscal(models.Model):
    _description = 'Operações Fiscais'
    _name = 'sped.operacao'
    _order = 'emissao, modelo, nome'
    _rec_name = 'nome'

    empresa_id = fields.Many2one('sped.empresa', 'Empresa', ondelete='restrict')
    modelo = fields.Selection(MODELO_FISCAL, 'Modelo', required=True, index=True, default=MODELO_FISCAL_NFE)
    emissao = fields.Selection(TIPO_EMISSAO, 'Tipo de emissão', index=True, default=TIPO_EMISSAO_PROPRIA)
    entrada_saida = fields.Selection(ENTRADA_SAIDA, 'Entrada/saída', index=True, default=ENTRADA_SAIDA_SAIDA)

    nome = fields.NameChar(string='Nome', size=120, index=True)
    codigo = fields.Char(string='Código', size=60, index=True)

    serie = fields.Char('Série', size=3)
    regime_tributario = fields.Selection(REGIME_TRIBUTARIO, 'Regime tributário', default=REGIME_TRIBUTARIO_SIMPLES)
    forma_pagamento = fields.Selection(FORMA_PAGAMENTO, 'Forma de pagamento', default=FORMA_PAGAMENTO_A_VISTA)
    finalidade_nfe = fields.Selection(FINALIDADE_NFE, 'Finalidade da NF-e', default=FINALIDADE_NFE_NORMAL)
    modalidade_frete = fields.Selection(MODALIDADE_FRETE, 'Modalidade do frete',
                                        default=MODALIDADE_FRETE_DESTINATARIO_PROPRIO)
    natureza_operacao_id = fields.Many2one('sped.natureza.operacao', 'Natureza da operação', ondelete='restrict')
    infadfisco = fields.Text('Informações adicionais de interesse do fisco')
    infcomplementar = fields.Text('Informações complementares')

    #
    # Retenção de impostos
    #
    deduz_retencao = fields.Boolean('Deduz retenção do total da NF?', default=True)
    pis_cofins_retido = fields.Boolean('PIS-COFINS retidos?')
    al_pis_retido = fields.Float('Alíquota do PIS', default=0.65, digits=(5, 2))
    al_cofins_retido = fields.Float('Alíquota da COFINS', default=3, digits=(5, 2))
    csll_retido = fields.Boolean('CSLL retido?')
    al_csll = fields.Float('Alíquota da CSLL', default=1, digits=(5, 2))

    #
    # Para todos os valores de referência numa operação fiscal, a moeda é SEMPRE o
    # Real BRL
    #
    currency_id = fields.Many2one('res.currency', 'Moeda', default=lambda self: self.env.ref('base.BRL').id)

    limite_retencao_pis_cofins_csll = fields.Monetary('Obedecer limite de faturamento para retenção de',
                                                      default=LIMITE_RETENCAO_PIS_COFINS_CSLL)

    irrf_retido = fields.Boolean('IR retido?')
    irrf_retido_ignora_limite = fields.Boolean('IR retido ignora limite de R$ 10,00?')
    al_irrf = fields.Float('Alíquota do IR', default=1, digits=(5, 2))

    #
    # Notas de serviço
    #
    inss_retido = fields.Boolean('INSS retido?')

    cnae_id = fields.Many2one('sped.cnae', 'CNAE')
    natureza_tributacao_nfse = fields.Selection(NATUREZA_TRIBUTACAO_NFSE, 'Natureza da tributação')
    servico_id = fields.Many2one('sped.servico', 'Serviço')
    cst_iss = fields.Selection(ST_ISS, 'CST ISS')

    # 'forca_recalculo_st_compra': fields.boolean('Força recálculo do ST na compra?'),
    # 'operacao_entrada_id': fields.many2one('sped.operacao', 'Operação de entrada equivalente'),

    consumidor_final = fields.Selection(TIPO_CONSUMIDOR_FINAL, 'Tipo do consumidor',
                                        default=TIPO_CONSUMIDOR_FINAL_NORMAL)
    presenca_comprador = fields.Selection(INDICADOR_PRESENCA_COMPRADOR, 'Presença do comprador',
                                          default=INDICADOR_PRESENCA_COMPRADOR_NAO_SE_APLICA)

    preco_automatico = fields.Selection([('V', 'Venda'), ('C', 'Custo')], 'Traz preço automático?')
