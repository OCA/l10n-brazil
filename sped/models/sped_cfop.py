# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia
#    Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from odoo import api, fields, models
from ..constante_tributaria import (
    CFOPS_CALCULA_SIMPLES_CSLL_IRPJ,
    CFOPS_COMPRA,
    CFOPS_COMPRA_ATIVO,
    CFOPS_COMPRA_COMERCIALIZACAO,
    CFOPS_COMPRA_CUSTO_VENDA,
    CFOPS_COMPRA_INDUSTRIALIZACAO,
    CFOPS_COMPRA_SERVICO,
    CFOPS_DEVOLUCAO_COMPRA,
    CFOPS_DEVOLUCAO_VENDA,
    CFOPS_RETORNO_ENTRADA,
    CFOPS_RETORNO_SAIDA,
    CFOPS_USO_CONSUMO,
    CFOPS_VENDA_ATIVO,
    CFOPS_VENDA_MERCADORIA,
    CFOPS_VENDA_SERVICO,
    ENTRADA_SAIDA,
    ENTRADA_SAIDA_SAIDA,
    POSICAO_CFOP,
)


class CFOP(models.Model):
    _description = u'CFOP'
    _name = 'sped.cfop'
    _rec_name = 'codigo'
    _order = 'codigo'

    codigo = fields.Char(
        string=u'Código',
        size=4,
        index=True,
        required=True,
    )
    descricao = fields.Char(
        string=u'Descrição',
        size=512,
        index=True,
        required=True,
    )
    entrada_saida = fields.Selection(
        selection=ENTRADA_SAIDA,
        string=u'Entrada/saída',
        index=True,
        default=ENTRADA_SAIDA_SAIDA,
    )
    posicao = fields.Selection(
        selection=POSICAO_CFOP,
        string=u'Posição',
        index=True,
    )
    gera_pis_cofins = fields.Boolean(
        string=u'Gera crédito de PIS-COFINS (entrada)/paga PIS-COFINS (saída)?'
    )
    natureza_bc_credito_pis_cofins = fields.Char(
        string=u'Natureza da BC do crédito de PIS-COFINS',
        size=2,
    )
    gera_ipi = fields.Boolean(
        string=u'Gera crédito de IPI (entrada)/paga IPI (saída)?',
    )
    gera_icms_proprio = fields.Boolean(
        string=u'Gera crédito de ICMS próprio (entrada)/paga ICMS próprio '
               u'(saída)?',
    )
    gera_icms_st = fields.Boolean(
        string=u'Gera crédito de ICMS ST (entrada)/paga ICMS ST (saída)?',
    )
    gera_icms_sn = fields.Boolean(
        string=u'Dá direito a crédito de ICMS SIMPLES (saída)?',
    )
    cfop_dentro_estado_id = fields.Many2one(
        comodel_name='sped.cfop',
        string=u'CFOP equivalente dentro do estado',
    )
    cfop_fora_estado_id = fields.Many2one(
        comodel_name='sped.cfop',
        string=u'CFOP equivalente para fora do estado',
    )
    cfop_fora_pais_id = fields.Many2one(
        comodel_name='sped.cfop',
        string=u'CFOP equivalente para fora do país'
    )
    cfop_entrada_id = fields.Many2one(
        comodel_name='sped.cfop',
        string=u'CFOP padrão para entrada'
    )
    movimentacao_fisica = fields.Boolean(
        comodel_name=u'Há movimentação física do produto?',
    )
    eh_compra = fields.Boolean(
        string=u'É compra?',
        compute='_compute_eh_compra_venda'
    )
    eh_compra_industrializacao = fields.Boolean(
        string=u'É compra para industrialização?',
        compute='_compute_eh_compra_venda',
    )
    eh_compra_comercializacao = fields.Boolean(
        string=u'É compra para comercialização?',
        compute='_compute_eh_compra_venda'
    )
    eh_compra_ativo = fields.Boolean(
        string=u'É compra de ativo?',
        compute='_compute_eh_compra_venda'
    )
    eh_compra_uso_consumo = fields.Boolean(
        string=u'É compra para uso e consumo?',
        compute='_compute_eh_compra_venda'
    )
    eh_compra_servico = fields.Boolean(
        string=u'É compra de serviço?',
        compute='_compute_eh_compra_venda'
    )
    custo_venda = fields.Boolean(
        string=u'Compõe custo para venda?',
        compute='_compute_eh_compra_venda',
    )
    eh_venda = fields.Boolean(
        string=u'É venda?',
        compute='_compute_eh_compra_venda'
    )
    eh_venda_mercadoria = fields.Boolean(
        string=u'É venda de mercadoria?',
        compute='_compute_eh_compra_venda'
    )
    eh_venda_ativo = fields.Boolean(
        string=u'É venda de ativo?',
        compute='_compute_eh_compra_venda'
    )
    eh_venda_servico = fields.Boolean(
        string=u'É venda de serviço?',
        compute='_compute_eh_compra_venda'
    )
    eh_devolucao_compra = fields.Boolean(
        string=u'É devolução de compra?',
        compute='_compute_eh_compra_venda'
    )
    eh_devolucao_venda = fields.Boolean(
        string=u'É devolução de venda?',
        compute='_compute_eh_compra_venda'
    )
    eh_retorno_entrada = fields.Boolean(
        string=u'É retorno entrada?',
        compute='_compute_eh_compra_venda'
    )
    eh_retorno_saida = fields.Boolean(
        string=u'É retorno saída?',
        compute='_compute_eh_compra_venda'
    )
    calcula_simples_csll_irpj = fields.Boolean(
        string=u'Calcula SIMPLES, CSLL e IRPJ?',
        compute='_compute_eh_compra_venda'
    )

    @api.multi
    def name_get(self):
        res = []

        for cfop in self:
            res.append((cfop.id, cfop.codigo + ' - ' + cfop.descricao))

        return res

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        if name and operator in ('=', 'ilike', '=ilike', 'like', 'ilike'):
            args = list(args or [])
            args = [
                '|',
                ('codigo', operator, name),
                ('descricao', operator, name),
            ] + args

            cfop_ids = self.search(args, limit=limit)

            if cfop_ids:
                return cfop_ids.name_get()

        return super(CFOP, self).name_search(
            name=name, args=args, operator=operator, limit=limit)

    @api.depends('codigo')
    def _compute_eh_compra_venda(self):
        for cfop in self:
            cfop.eh_compra = cfop.codigo in CFOPS_COMPRA
            cfop.eh_compra_industrializacao = (
                cfop.codigo in CFOPS_COMPRA_INDUSTRIALIZACAO)
            cfop.eh_compra_comercializacao = (
                cfop.codigo in CFOPS_COMPRA_COMERCIALIZACAO)
            cfop.eh_compra_ativo = cfop.codigo in CFOPS_COMPRA_ATIVO
            cfop.eh_compra_uso_consumo = cfop.codigo in CFOPS_USO_CONSUMO
            cfop.eh_compra_servico = cfop.codigo in CFOPS_COMPRA_SERVICO
            cfop.custo_venda = cfop.codigo in CFOPS_COMPRA_CUSTO_VENDA

            cfop.eh_venda = (cfop.codigo in CFOPS_VENDA_MERCADORIA) or (
                cfop.codigo in CFOPS_VENDA_ATIVO) or \
                (cfop.codigo in CFOPS_VENDA_SERVICO)
            cfop.eh_venda_mercadoria = cfop.codigo in CFOPS_VENDA_MERCADORIA
            cfop.eh_venda_ativo = cfop.codigo in CFOPS_VENDA_ATIVO
            cfop.eh_venda_servico = cfop.codigo in CFOPS_VENDA_SERVICO

            cfop.eh_devolucao_compra = cfop.codigo in CFOPS_DEVOLUCAO_COMPRA
            cfop.eh_devolucao_venda = cfop.codigo in CFOPS_DEVOLUCAO_VENDA

            cfop.eh_retorno_entrada = cfop.codigo in CFOPS_RETORNO_ENTRADA
            cfop.eh_retorno_saida = cfop.codigo in CFOPS_RETORNO_SAIDA

            cfop.calcula_simples_csll_irpj = (
                cfop.codigo in CFOPS_CALCULA_SIMPLES_CSLL_IRPJ)
