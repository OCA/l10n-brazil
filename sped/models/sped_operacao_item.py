# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia - Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#


from __future__ import division, print_function, unicode_literals
from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
from ..constante_tributaria import *


class OperacaoFiscalItem(models.Model):
    _description = 'Operações Fiscais - Itens'
    _name = 'sped.operacao.item'
    _order = 'operacao_id, protocolo_id, contribuinte, cfop_codigo'
    #_rec_name = 'nome'

    operacao_id = fields.Many2one('sped.operacao', 'Operação', ondelete='cascade')
    entrada_saida = fields.Selection(ENTRADA_SAIDA, 'Entrada/saída', related='operacao_id.entrada_saida', readonly=True)
    tipo_protocolo = fields.Selection([('P', 'Próprio'), ('S', 'ST')], 'Tipo do protocolo', index=True)
    protocolo_id = fields.Many2one('sped.protocolo.icms', 'Protocolo')
    cfop_id = fields.Many2one('sped.cfop', 'CFOP', required=True, ondelete='restrict')
    cfop_codigo = fields.Char('CFOP', related='cfop_id.codigo', size=4, store=True, index=True)
    compoe_total = fields.Boolean('Compõe o valor total da nota?', default=True)
    movimentacao_fisica = fields.Boolean('Há movimentação física do produto?', default=True)
    contribuinte = fields.Selection(IE_DESTINATARIO, 'Contribuinte', index=True)
    org_icms = fields.Selection(ORIGEM_MERCADORIA, 'Origem da mercadoria', index=True)
    cst_icms = fields.Selection(ST_ICMS, 'CST ICMS', default=ST_ICMS_INTEGRAL)
    cst_icms_sn = fields.Selection(ST_ICMS_SN, 'CSOSN', default=ST_ICMS_SN_TRIB_SEM_CREDITO)
    cst_ipi = fields.Selection(ST_IPI, 'CST IPI')
    cst_ipi_entrada = fields.Selection(ST_IPI_ENTRADA, 'CST IPI')
    cst_ipi_saida = fields.Selection(ST_IPI_SAIDA, 'CST IPI')
    bc_icms_proprio_com_ipi = fields.Boolean('IPI integra a BC do ICMS?')
    bc_icms_st_com_ipi = fields.Boolean('IPI integra a BC do ICMS ST?')
    al_pis_cofins_id = fields.Many2one('sped.aliquota.pis.cofins', 'CST PIS-COFINS')

    protocolo_alternativo_id = fields.Many2one('sped.protocolo.icms', 'Protocolo alternativo')

    @api.depends('cfop_id')
    @api.onchange('cst_icms_sn')
    def onchange_cst_icms_sn(self):
        res = {}
        valores = {}
        res['value'] = valores

        if self.cst_icms_sn in ST_ICMS_SN_CALCULA_CREDITO:
            if not self.cfop_id.eh_venda:
                raise ValidationError('Você selecionou uma CSOSN que dá direito a crédito, porém a CFOP não indica uma venda!')

        return res

    @api.onchange('cst_ipi_entrada')
    def onchange_cst_ipi_entrada(self):
        return {'value': {'cst_ipi': self.cst_ipi_entrada}}

    @api.onchange('cst_ipi_saida')
    def onchange_cst_ipi_saida(self):
        return {'value': {'cst_ipi': self.cst_ipi_saida}}


class OperacaoFiscal(models.Model):
    _name = 'sped.operacao'
    _inherit = 'sped.operacao'

    item_ids = fields.One2many('sped.operacao.item', 'operacao_id', string='Itens')
    item_simples_ids = fields.One2many('sped.operacao.item', 'operacao_id', string='Itens')

    item_sem_st_ids = fields.One2many('sped.operacao.item', 'operacao_id', string='Itens', domain=[('tipo_protocolo', '=', 'P')])
    item_simples_sem_st_ids = fields.One2many('sped.operacao.item', 'operacao_id', string='Itens', domain=[('tipo_protocolo', '=', 'P')])

    item_com_st_ids = fields.One2many('sped.operacao.item', 'operacao_id', string='Itens', domain=[('tipo_protocolo', '=', 'S')])
    item_simples_com_st_ids = fields.One2many('sped.operacao.item', 'operacao_id', string='Itens', domain=[('tipo_protocolo', '=', 'S')])
