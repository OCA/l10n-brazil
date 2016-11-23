# -*- coding: utf-8 -*-


from __future__ import division, print_function, unicode_literals
from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
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
    #dentro_estado = fields.Boolean('Dentro do estado?', index=True)
    #fora_estado = fields.Boolean('Fora do estado?', index=True)
    #fora_pais = fields.Boolean('Fora do país?', index=True)
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
    #nome': fields.function(_get_nome_funcao, type='char', string='Nome', fnct_search=_procura_nome),

    #_sql_constraints = [
        #('codigo_unique', 'unique (codigo)', 'O código não pode se repetir!'),
    #]

    @api.one
    @api.depends('codigo')
    def _eh_compra_venda(self):
        self.eh_compra = self.codigo in CFOPS_COMPRA
        self.eh_compra_industrializacao = self.codigo in CFOPS_COMPRA_INDUSTRIALIZACAO
        self.eh_compra_comercializacao = self.codigo in CFOPS_COMPRA_COMERCIALIZACAO
        self.eh_compra_ativo = self.codigo in CFOPS_COMPRA_ATIVO
        self.eh_compra_uso_consumo = self.codigo in CFOPS_USO_CONSUMO
        self.eh_compra_servico = self.codigo in CFOPS_COMPRA_SERVICO
        self.custo_venda = self.codigo in CFOPS_COMPRA_CUSTO_VENDA

        self.eh_venda = self.codigo in CFOPS_VENDA_MERCADORIA or self.codigo in CFOPS_VENDA_ATIVO or self.codigo in CFOPS_VENDA_SERVICO
        self.eh_venda_mercadoria = self.codigo in CFOPS_VENDA_MERCADORIA
        self.eh_venda_ativo = self.codigo in CFOPS_VENDA_ATIVO
        self.eh_venda_servico = self.codigo in CFOPS_VENDA_SERVICO

        self.eh_devolucao_compra = self.codigo in CFOPS_DEVOLUCAO_COMPRA
        self.eh_devolucao_venda = self.codigo in CFOPS_DEVOLUCAO_VENDA

        self.calcula_simples_csll_irpj = self.codigo in CFOPS_CALCULA_SIMPLES_CSLL_IRPJ

    eh_compra = fields.Boolean('É compra?', compute=_eh_compra_venda)
    eh_compra_industrializacao = fields.Boolean('É compra para industrialização?', compute=_eh_compra_venda)
    eh_compra_comercializacao = fields.Boolean('É compra para comercialização?', compute=_eh_compra_venda)
    eh_compra_ativo = fields.Boolean('É compra de ativo?', compute=_eh_compra_venda)
    eh_compra_uso_consumo = fields.Boolean('É compra para uso e consumo?', compute=_eh_compra_venda)
    eh_compra_servico = fields.Boolean('É compra de serviço?', compute=_eh_compra_venda)
    custo_venda = fields.Boolean('Compõe custo para venda?', compute=_eh_compra_venda)

    eh_venda = fields.Boolean('É venda?', compute=_eh_compra_venda)
    eh_venda_mercadoria = fields.Boolean('É venda de mercadoria?', compute=_eh_compra_venda)
    eh_venda_ativo = fields.Boolean('É venda de ativo?', compute=_eh_compra_venda)
    eh_venda_servico = fields.Boolean('É venda de serviço?', compute=_eh_compra_venda)

    eh_devolucao_compra = fields.Boolean('É devolução de compra?', compute=_eh_compra_venda)
    eh_devolucao_venda = fields.Boolean('É devolução de venda?', compute=_eh_compra_venda)

    calcula_simples_csll_irpj = fields.Boolean('Calcula SIMPLES, CSLL e IRPJ?', compute=_eh_compra_venda)
