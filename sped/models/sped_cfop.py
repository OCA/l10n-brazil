# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia - Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#


from __future__ import division, print_function, unicode_literals

from odoo import api, fields, models
from ..constante_tributaria import *


class CFOP(models.Model):
    _description = 'CFOP'
    _name = 'sped.cfop'
    _rec_name = 'codigo'
    _order = 'codigo'

    codigo = fields.UpperChar('Código', size=4, index=True, required=True)
    descricao = fields.Char('Descrição', size=512, index=True, required=True)
    entrada_saida = fields.Selection(ENTRADA_SAIDA, 'Entrada/saída', index=True, default=ENTRADA_SAIDA_SAIDA)
    posicao = fields.Selection(POSICAO_CFOP, 'Posição', index=True)
    gera_pis_cofins = fields.Boolean('Gera crédito de PIS-COFINS (entrada)/paga PIS-COFINS (saída)?')
    natureza_bc_credito_pis_cofins = fields.Char('Natureza da BC do crédito de PIS-COFINS', size=2)
    gera_ipi = fields.Boolean('Gera crédito de IPI (entrada)/paga IPI (saída)?')
    gera_icms_proprio = fields.Boolean('Gera crédito de ICMS próprio (entrada)/paga ICMS próprio (saída)?')
    gera_icms_st = fields.Boolean('Gera crédito de ICMS ST (entrada)/paga ICMS ST (saída)?')
    gera_icms_sn = fields.Boolean('Dá direito a crédito de ICMS SIMPLES (saída)?')
    cfop_dentro_estado_id = fields.Many2one('sped.cfop', 'CFOP equivalente dentro do estado')
    cfop_fora_estado_id = fields.Many2one('sped.cfop', 'CFOP equivalente para fora do estado')
    cfop_fora_pais_id = fields.Many2one('sped.cfop', 'CFOP equivalente para fora do país')
    cfop_entrada_id = fields.Many2one('sped.cfop', 'CFOP padrão para entrada')
    movimentacao_fisica = fields.Boolean('Há movimentação física do produto?')

    eh_compra = fields.Boolean('É compra?', compute='_compute_eh_compra_venda')
    eh_compra_industrializacao = fields.Boolean('É compra para industrialização?', compute='_compute_eh_compra_venda')
    eh_compra_comercializacao = fields.Boolean('É compra para comercialização?', compute='_compute_eh_compra_venda')
    eh_compra_ativo = fields.Boolean('É compra de ativo?', compute='_compute_eh_compra_venda')
    eh_compra_uso_consumo = fields.Boolean('É compra para uso e consumo?', compute='_compute_eh_compra_venda')
    eh_compra_servico = fields.Boolean('É compra de serviço?', compute='_compute_eh_compra_venda')
    custo_venda = fields.Boolean('Compõe custo para venda?', compute='_compute_eh_compra_venda')

    eh_venda = fields.Boolean('É venda?', compute='_compute_eh_compra_venda')
    eh_venda_mercadoria = fields.Boolean('É venda de mercadoria?', compute='_compute_eh_compra_venda')
    eh_venda_ativo = fields.Boolean('É venda de ativo?', compute='_compute_eh_compra_venda')
    eh_venda_servico = fields.Boolean('É venda de serviço?', compute='_compute_eh_compra_venda')

    eh_devolucao_compra = fields.Boolean('É devolução de compra?', compute='_compute_eh_compra_venda')
    eh_devolucao_venda = fields.Boolean('É devolução de venda?', compute='_compute_eh_compra_venda')

    eh_retorno_entrada = fields.Boolean('É retorno entrada?', compute='_compute_eh_compra_venda')
    eh_retorno_saida = fields.Boolean('É retorno saída?', compute='_compute_eh_compra_venda')

    calcula_simples_csll_irpj = fields.Boolean('Calcula SIMPLES, CSLL e IRPJ?', compute='_compute_eh_compra_venda')

    @api.depends('codigo')
    def _compute_eh_compra_venda(self):
        for cfop in self:
            cfop.eh_compra = cfop.codigo in CFOPS_COMPRA
            cfop.eh_compra_industrializacao = cfop.codigo in CFOPS_COMPRA_INDUSTRIALIZACAO
            cfop.eh_compra_comercializacao = cfop.codigo in CFOPS_COMPRA_COMERCIALIZACAO
            cfop.eh_compra_ativo = cfop.codigo in CFOPS_COMPRA_ATIVO
            cfop.eh_compra_uso_consumo = cfop.codigo in CFOPS_USO_CONSUMO
            cfop.eh_compra_servico = cfop.codigo in CFOPS_COMPRA_SERVICO
            cfop.custo_venda = cfop.codigo in CFOPS_COMPRA_CUSTO_VENDA

            cfop.eh_venda = (cfop.codigo in CFOPS_VENDA_MERCADORIA) or (cfop.codigo in CFOPS_VENDA_ATIVO) or \
                            (cfop.codigo in CFOPS_VENDA_SERVICO)
            cfop.eh_venda_mercadoria = cfop.codigo in CFOPS_VENDA_MERCADORIA
            cfop.eh_venda_ativo = cfop.codigo in CFOPS_VENDA_ATIVO
            cfop.eh_venda_servico = cfop.codigo in CFOPS_VENDA_SERVICO

            cfop.eh_devolucao_compra = cfop.codigo in CFOPS_DEVOLUCAO_COMPRA
            cfop.eh_devolucao_venda = cfop.codigo in CFOPS_DEVOLUCAO_VENDA

            cfop.eh_retorno_entrada = cfop.codigo in CFOPS_RETORNO_ENTRADA
            cfop.eh_retorno_saida = cfop.codigo in CFOPS_RETORNO_SAIDA

            cfop.calcula_simples_csll_irpj = cfop.codigo in CFOPS_CALCULA_SIMPLES_CSLL_IRPJ
