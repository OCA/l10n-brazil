# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia
#   Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#


from odoo import api, fields, models
from odoo.exceptions import ValidationError

from ..constante_tributaria import (
    ENTRADA_SAIDA,
    IE_DESTINATARIO,
    ORIGEM_MERCADORIA,
    ST_ICMS,
    ST_ICMS_INTEGRAL,
    ST_ICMS_SN,
    ST_ICMS_SN_CALCULA_CREDITO,
    ST_ICMS_SN_TRIB_SEM_CREDITO,
    ST_IPI,
    ST_IPI_ENTRADA,
    ST_IPI_SAIDA,
)


class OperacaoFiscalItem(models.Model):
    _description = u'Operações Fiscais - Itens'
    _name = 'sped.operacao.item'
    _order = 'operacao_id, protocolo_id, contribuinte, cfop_codigo'
    # _rec_name = 'nome'

    operacao_id = fields.Many2one(
        comodel_name='sped.operacao',
        string=u'Operação',
        ondelete='cascade',
    )
    entrada_saida = fields.Selection(
        selection=ENTRADA_SAIDA,
        string=u'Entrada/saída',
        related='operacao_id.entrada_saida',
        readonly=True,
    )
    tipo_protocolo = fields.Selection([
        ('P', u'Próprio'),
        ('S', u'ST')
    ],
        string=u'Tipo do protocolo',
        index=True,
    )
    protocolo_id = fields.Many2one(
        comodel_name='sped.protocolo.icms',
        string=u'Protocolo',
    )
    cfop_id = fields.Many2one(
        comodel_name='sped.cfop',
        string=u'CFOP',
        required=True,
        ondelete='restrict',
    )
    cfop_codigo = fields.Char(
        string=u'CFOP',
        related='cfop_id.codigo',
        size=4,
        store=True,
        index=True,
    )
    compoe_total = fields.Boolean(
        string=u'Compõe o valor total da nota?',
        default=True,
    )
    movimentacao_fisica = fields.Boolean(
        string=u'Há movimentação física do produto?',
        default=True,
    )
    contribuinte = fields.Selection(
        selection=IE_DESTINATARIO,
        string=u'Contribuinte',
        index=True,
    )
    org_icms = fields.Selection(
        selection=ORIGEM_MERCADORIA,
        string=u'Origem da mercadoria',
        index=True,
    )
    cst_icms = fields.Selection(
        selection=ST_ICMS,
        string=u'CST ICMS',
        default=ST_ICMS_INTEGRAL,
    )
    cst_icms_sn = fields.Selection(
        selection=ST_ICMS_SN,
        string=u'CSOSN',
        default=ST_ICMS_SN_TRIB_SEM_CREDITO,
    )
    cst_ipi = fields.Selection(
        selection=ST_IPI,
        string=u'CST IPI',
    )
    cst_ipi_entrada = fields.Selection(
        selection=ST_IPI_ENTRADA,
        string=u'CST IPI',
    )
    cst_ipi_saida = fields.Selection(
        selection=ST_IPI_SAIDA,
        string=u'CST IPI'
    )
    bc_icms_proprio_com_ipi = fields.Boolean(
        string=u'IPI integra a BC do ICMS?'
    )
    bc_icms_st_com_ipi = fields.Boolean(
        string=u'IPI integra a BC do ICMS ST?'
    )
    al_pis_cofins_id = fields.Many2one(
        comodel_name='sped.aliquota.pis.cofins',
        string=u'CST PIS-COFINS'
    )
    protocolo_alternativo_id = fields.Many2one(
        comodel_name='sped.protocolo.icms',
        string=u'Protocolo alternativo'
    )

    @api.depends('cfop_id')
    @api.onchange('cst_icms_sn')
    def onchange_cst_icms_sn(self):
        res = {}
        valores = {}
        res['value'] = valores

        if self.cst_icms_sn in ST_ICMS_SN_CALCULA_CREDITO:
            if not self.cfop_id.eh_venda:
                raise ValidationError("""
                Você selecionou uma CSOSN que dá direito a crédito, porém a
                CFOP não indica uma venda!""")

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

    item_ids = fields.One2many(
        comodel_name='sped.operacao.item',
        inverse_name='operacao_id',
        string=u'Item da operação fiscal',
    )
    item_simples_ids = fields.One2many(
        comodel_name='sped.operacao.item',
        inverse_name='operacao_id',
        string=u'Item da operação fiscal'
    )
    item_sem_st_ids = fields.One2many(
        comodel_name='sped.operacao.item',
        inverse_name='operacao_id',
        string=u'Item da operação fiscal',
        domain=[('tipo_protocolo', '=', 'P')],
    )
    item_simples_sem_st_ids = fields.One2many(
        comodel_name='sped.operacao.item',
        inverse_name='operacao_id',
        string=u'Item da operação fiscal',
        domain=[('tipo_protocolo', '=', 'P')],
    )

    item_com_st_ids = fields.One2many(
        comodel_name='sped.operacao.item',
        inverse_name='operacao_id',
        string=u'Item da operação fiscal',
        domain=[('tipo_protocolo', '=', 'S')]
    )
    item_simples_com_st_ids = fields.One2many(
        comodel_name='sped.operacao.item',
        inverse_name='operacao_id',
        string=u'Item da operação fiscal',
        domain=[('tipo_protocolo', '=', 'S')]
    )
