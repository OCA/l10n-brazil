# -*- coding: utf-8 -*-


from __future__ import division, print_function, unicode_literals
from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
from ..constante_tributaria import *
from pybrasil.valor.decimal import Decimal as D


class OperacaoFiscal(models.Model):
    _description = 'Operações Fiscais'
    _name = 'sped.operacao'
    _order = 'emissao, modelo, nome'
    _rec_name = 'nome'

    company_id = fields.Many2one('res.company', 'Empresa', ondelete='restrict', default=lambda self: self.env['res.company']._company_default_get('sped.operacao'))
    modelo = fields.Selection(MODELO_FISCAL, 'Modelo', required=True, index=True, default=MODELO_FISCAL_NFE)
    emissao = fields.Selection(TIPO_EMISSAO, 'Tipo de emissão', index=True, default=TIPO_EMISSAO_PROPRIA)
    entrada_saida = fields.Selection(ENTRADA_SAIDA, 'Entrada/saída', index=True, default=ENTRADA_SAIDA_SAIDA)

    nome = fields.NameChar(string='Nome', size=120, index=True)
    codigo = fields.Char(string='Código', size=60, index=True)

    serie = fields.Char('Série', size=3)
    regime_tributario = fields.Selection(REGIME_TRIBUTARIO, 'Regime tributário', default=REGIME_TRIBUTARIO_SIMPLES)
    forma_pagamento = fields.Selection(FORMA_PAGAMENTO, 'Forma de pagamento', default=FORMA_PAGAMENTO_A_VISTA)
    finalidade_nfe = fields.Selection(FINALIDADE_NFE, 'Finalidade da NF-e', default=FINALIDADE_NFE_NORMAL)
    modalidade_frete = fields.Selection(MODALIDADE_FRETE, 'Modalidade do frete', default=MODALIDADE_FRETE_DESTINATARIO)
    natureza_operacao_id = fields.Many2one('sped.natureza.operacao', 'Natureza da operação', ondelete='restrict')
    infadfisco =  fields.Text('Informações adicionais de interesse do fisco')
    infcomplementar = fields.Text('Informações complementares')

    #
    # Retenção de impostos
    #
    deduz_retencao = fields.Boolean('Deduz retenção do total da NF?', default=True)
    pis_cofins_retido = fields.Boolean('PIS-COFINS retidos?')
    al_pis_retido = fields.Porcentagem('Alíquota do PIS', default=0.65)
    al_cofins_retido = fields.Porcentagem('Alíquota da COFINS', default=3)
    csll_retido = fields.Boolean('CSLL retido?')
    al_csll =  fields.Porcentagem('Alíquota da CSLL', default=1)
    limite_retencao_pis_cofins_csll = fields.Dinheiro('Obedecer limite de faturamento para retenção de', default=5000)

    irrf_retido = fields.Boolean('IR retido?')
    irrf_retido_ignora_limite = fields.Boolean('IR retido ignora limite de R$ 10,00?')
    al_irrf =  fields.Porcentagem('Alíquota do IR', default=1)


    #
    # Notas de serviço
    #
    previdencia_retido = fields.Boolean('INSS retido?')

    cnae_id = fields.Many2one('sped.cnae', 'CNAE')
    natureza_tributacao_nfse = fields.Selection(NATUREZA_TRIBUTACAO_NFSE, 'Natureza da tributação')
    servico_id = fields.Many2one('sped.servico', 'Serviço')
    cst_iss = fields.Selection(ST_ISS, 'CST ISS')

    #'prioriza_familia_ncm': fields.boolean('Prioriza família tributária por NCM?'),
    #'user_ids': fields.many2many('res.users', 'sped_operacao_usuario', 'sped_operacao_id', 'res_user_id', 'Usuários permitidos'),
    #'company_ids': fields.many2many('res.company', 'sped_operacao_company', 'sped_operacao_id', 'company_id', 'Empresas permitidas'),
    #'forca_recalculo_st_compra': fields.boolean('Força recálculo do ST na compra?'),
    #'calcula_diferencial_aliquota': fields.boolean('Calcula diferencial de alíquota?'),
    #'operacao_entrada_id': fields.many2one('sped.operacao', 'Operação de entrada equivalente'),
