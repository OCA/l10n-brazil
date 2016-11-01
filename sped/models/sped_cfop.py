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
    dentro_estado = fields.Boolean('Dentro do estado?', index=True)
    fora_estado = fields.Boolean('Fora do estado?', index=True)
    fora_pais = fields.Boolean('Fora do país?', index=True)
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
