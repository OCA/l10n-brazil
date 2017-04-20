# -*- coding: utf-8 -*-


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
    tipo_protocolo = fields.Selection([('P', 'Próprio'), ('S', 'ST')], 'Tipo do protocolo', index=True)
    protocolo_id = fields.Many2one('sped.protocolo.icms', 'Protocolo')
    cfop_id = fields.Many2one('sped.cfop', 'CFOP', required=True, ondelete='restrict')
    cfop_codigo = fields.Char('CFOP', related='cfop_id.codigo', size=4, store=True, index=True)
    cfop_dentro_estado = fields.Boolean('Dentro do estado?', related='cfop_id.dentro_estado', store=True, index=True)
    cfop_fora_estado = fields.Boolean('Fora do estado?', related='cfop_id.fora_estado', store=True, index=True)
    cfop_fora_pais = fields.Boolean('Fora do país?', related='cfop_id.fora_pais', store=True, index=True)

    compoe_total = fields.Boolean('Compõe o valor total da nota?', default=True)
    movimentacao_fisica = fields.Boolean('Há movimentação física do produto?', default=True)
    contribuinte = fields.Selection(IE_DESTINATARIO, 'Contribuinte', index=True)
    org_icms = fields.Selection(ORIGEM_MERCADORIA, 'Origem da mercadoria', index=True)
    cst_icms = fields.Selection(ST_ICMS, 'CST ICMS', default=ST_ICMS_INTEGRAL)
    cst_icms_sn = fields.Selection(ST_ICMS_SN, 'CSOSN', default=ST_ICMS_SN_TRIB_SEM_CREDITO)
    cst_ipi = fields.Selection(ST_IPI, 'CST IPI')
    bc_icms_proprio_com_ipi = fields.Boolean('IPI integra a BC do ICMS?')
    bc_icms_st_com_ipi = fields.Boolean('IPI integra a BC do ICMS ST?')
    al_pis_cofins_id = fields.Many2one('sped.aliquota.pis.cofins', 'CST PIS-COFINS')

    protocolo_alternativo_id = fields.Many2one('sped.protocolo.icms', 'Protocolo alternativo')


class OperacaoFiscal(models.Model):
    _name = 'sped.operacao'
    _inherit = 'sped.operacao'

    item_ids = fields.One2many('sped.operacao.item', 'operacao_id', string='Itens')
    item_simples_ids = fields.One2many('sped.operacao.item', 'operacao_id', string='Itens')

    item_sem_st_ids = fields.One2many('sped.operacao.item', 'operacao_id', string='Itens', domain=[('tipo_protocolo', '=', 'P')])
    item_simples_sem_st_ids = fields.One2many('sped.operacao.item', 'operacao_id', string='Itens', domain=[('tipo_protocolo', '=', 'P')])

    item_com_st_ids = fields.One2many('sped.operacao.item', 'operacao_id', string='Itens', domain=[('tipo_protocolo', '=', 'S')])
    item_simples_com_st_ids = fields.One2many('sped.operacao.item', 'operacao_id', string='Itens', domain=[('tipo_protocolo', '=', 'S')])
