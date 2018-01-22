# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia
#    Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from __future__ import division, print_function, unicode_literals

from odoo import api, fields, models
from odoo.addons.l10n_br_base.constante_tributaria import (
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


class SpedCFOP(models.Model):
    _name = b'sped.cfop'
    _description = 'CFOPs'
    _rec_name = 'codigo'
    _order = 'codigo'

    codigo = fields.Char(
        string='Código',
        size=4,
        index=True,
        required=True,
    )
    descricao = fields.Char(
        string='Descrição',
        size=512,
        index=True,
        required=True,
    )
    entrada_saida = fields.Selection(
        selection=ENTRADA_SAIDA,
        string='Entrada/saída',
        index=True,
        default=ENTRADA_SAIDA_SAIDA,
    )
    posicao = fields.Selection(
        selection=POSICAO_CFOP,
        string='Posição',
        index=True,
    )
    gera_pis_cofins = fields.Boolean(
        string='Gera crédito de PIS-COFINS (entrada)/paga PIS-COFINS (saída)?'
    )
    natureza_bc_credito_pis_cofins = fields.Char(
        string='Natureza da BC do crédito de PIS-COFINS',
        size=2,
    )
    gera_ipi = fields.Boolean(
        string='Gera crédito de IPI (entrada)/paga IPI (saída)?',
    )
    gera_icms_proprio = fields.Boolean(
        string='Gera crédito de ICMS próprio (entrada)/paga ICMS próprio '
               '(saída)?',
    )
    gera_icms_st = fields.Boolean(
        string='Gera crédito de ICMS ST (entrada)/paga ICMS ST (saída)?',
    )
    gera_icms_sn = fields.Boolean(
        string='Dá direito a crédito de ICMS SIMPLES (saída)?',
    )
    cfop_dentro_estado_id = fields.Many2one(
        comodel_name='sped.cfop',
        string='CFOP equivalente dentro do estado',
    )
    cfop_fora_estado_id = fields.Many2one(
        comodel_name='sped.cfop',
        string='CFOP equivalente para fora do estado',
    )
    cfop_fora_pais_id = fields.Many2one(
        comodel_name='sped.cfop',
        string='CFOP equivalente para fora do país'
    )
    cfop_entrada_id = fields.Many2one(
        comodel_name='sped.cfop',
        string='CFOP padrão para entrada'
    )
    movimentacao_fisica = fields.Boolean(
        comodel_name='Há movimentação física do produto?',
    )
    eh_compra = fields.Boolean(
        string='É compra?',
        compute='_compute_eh_compra_venda',
        store=True,
    )
    eh_compra_industrializacao = fields.Boolean(
        string='É compra para industrialização?',
        compute='_compute_eh_compra_venda',
        store=True,
    )
    eh_compra_comercializacao = fields.Boolean(
        string='É compra para comercialização?',
        compute='_compute_eh_compra_venda',
        store=True,
    )
    eh_compra_ativo = fields.Boolean(
        string='É compra de ativo?',
        compute='_compute_eh_compra_venda',
        store=True,
    )
    eh_compra_uso_consumo = fields.Boolean(
        string='É compra para uso e consumo?',
        compute='_compute_eh_compra_venda',
        store=True,
    )
    eh_compra_servico = fields.Boolean(
        string='É compra de serviço?',
        compute='_compute_eh_compra_venda',
        store=True,
    )
    custo_venda = fields.Boolean(
        string='Compõe custo para venda?',
        compute='_compute_eh_compra_venda',
        store=True,
    )
    eh_venda = fields.Boolean(
        string='É venda?',
        compute='_compute_eh_compra_venda',
        store=True,
    )
    eh_venda_mercadoria = fields.Boolean(
        string='É venda de mercadoria?',
        compute='_compute_eh_compra_venda',
        store=True,
    )
    eh_venda_ativo = fields.Boolean(
        string='É venda de ativo?',
        compute='_compute_eh_compra_venda',
        store=True,
    )
    eh_venda_servico = fields.Boolean(
        string='É venda de serviço?',
        compute='_compute_eh_compra_venda',
        store=True,
    )
    eh_devolucao_compra = fields.Boolean(
        string='É devolução de compra?',
        compute='_compute_eh_compra_venda',
        store=True,
    )
    eh_devolucao_venda = fields.Boolean(
        string='É devolução de venda?',
        compute='_compute_eh_compra_venda',
        store=True,
    )
    eh_retorno_entrada = fields.Boolean(
        string='É retorno entrada?',
        compute='_compute_eh_compra_venda',
        store=True,
    )
    eh_retorno_saida = fields.Boolean(
        string='É retorno saída?',
        compute='_compute_eh_compra_venda',
        store=True,
    )
    calcula_simples_csll_irpj = fields.Boolean(
        string='Calcula SIMPLES, CSLL e IRPJ?',
        compute='_compute_eh_compra_venda',
        store=True,
    )

    @api.multi
    def name_get(self):
        res = []

        for cfop in self:
            if self._context.get('cfop_tam_desc') == 'curta':
                res.append((cfop.id, cfop.codigo))
            else:
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
            return cfop_ids.name_get()

        return super(SpedCFOP, self).name_search(
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
