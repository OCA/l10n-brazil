# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia
#   Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from __future__ import division, print_function, unicode_literals

from odoo import api, fields, models
from odoo.exceptions import ValidationError

from odoo.addons.l10n_br_base.constante_tributaria import (
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
    TIPO_PRODUTO_SERVICO
)


class SpedOperacaoFiscalItem(models.Model):
    _name = b'sped.operacao.item'
    _description = 'Itens da Operação Fiscal'
    _order = 'operacao_id, protocolo_id, contribuinte, cfop_codigo'
    # _rec_name = 'nome'

    operacao_id = fields.Many2one(
        comodel_name='sped.operacao',
        string='Operação',
        ondelete='cascade',
    )
    entrada_saida = fields.Selection(
        selection=ENTRADA_SAIDA,
        string='Entrada/saída',
        related='operacao_id.entrada_saida',
        readonly=True,
    )

    #
    # Filtro
    #
    tipo_protocolo = fields.Selection([
        ('P', 'Próprio'),
        ('S', 'ST')
    ],
        string='Tipo do protocolo',
        index=True,
    )
    protocolo_id = fields.Many2one(
        comodel_name='sped.protocolo.icms',
        string='Protocolo',
    )
    contribuinte = fields.Selection(
        selection=IE_DESTINATARIO,
        string='Contribuinte',
        index=True,
    )
    tipo_produto_servico = fields.Selection(
        selection=TIPO_PRODUTO_SERVICO,
        string='Tipo do produto/serviço',
        index=True
    )

    #
    # Configuração do item
    #
    cfop_id = fields.Many2one(
        comodel_name='sped.cfop',
        string='CFOP',
        required=True,
        ondelete='restrict',
    )
    cfop_codigo = fields.Char(
        string='CFOP',
        related='cfop_id.codigo',
        size=4,
        store=True,
        index=True,
    )
    compoe_total = fields.Boolean(
        string='Compõe o valor total da nota?',
        default=True,
    )
    movimentacao_fisica = fields.Boolean(
        string='Há movimentação física do produto?',
        default=True,
    )
    org_icms = fields.Selection(
        selection=ORIGEM_MERCADORIA,
        string='Origem da mercadoria',
        index=True,
    )
    cst_icms = fields.Selection(
        selection=ST_ICMS,
        string='CST ICMS',
        default=ST_ICMS_INTEGRAL,
    )
    cst_icms_sn = fields.Selection(
        selection=ST_ICMS_SN,
        string='CSOSN',
        default=ST_ICMS_SN_TRIB_SEM_CREDITO,
    )
    cst_ipi = fields.Selection(
        selection=ST_IPI,
        string='CST IPI',
    )
    cst_ipi_entrada = fields.Selection(
        selection=ST_IPI_ENTRADA,
        string='CST IPI',
    )
    cst_ipi_saida = fields.Selection(
        selection=ST_IPI_SAIDA,
        string='CST IPI'
    )
    bc_icms_proprio_com_ipi = fields.Boolean(
        string='IPI integra a BC do ICMS?'
    )
    bc_icms_st_com_ipi = fields.Boolean(
        string='IPI integra a BC do ICMS ST?'
    )
    enquadramento_ipi = fields.Char(
        string='Enquadramento legal do IPI',
        size=3
    )
    al_pis_cofins_id = fields.Many2one(
        comodel_name='sped.aliquota.pis.cofins',
        string='CST PIS-COFINS'
    )
    protocolo_alternativo_id = fields.Many2one(
        comodel_name='sped.protocolo.icms',
        string='Protocolo alternativo'
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


class SpedOperacaoFiscal(models.Model):
    _name = b'sped.operacao'
    _inherit = 'sped.operacao'

    item_ids = fields.One2many(
        comodel_name='sped.operacao.item',
        inverse_name='operacao_id',
        string='Item da operação fiscal',
    )
    item_simples_ids = fields.One2many(
        comodel_name='sped.operacao.item',
        inverse_name='operacao_id',
        string='Item da operação fiscal'
    )
    item_sem_st_ids = fields.One2many(
        comodel_name='sped.operacao.item',
        inverse_name='operacao_id',
        string='Item da operação fiscal',
        domain=[('tipo_protocolo', '=', 'P')],
    )
    item_simples_sem_st_ids = fields.One2many(
        comodel_name='sped.operacao.item',
        inverse_name='operacao_id',
        string='Item da operação fiscal',
        domain=[('tipo_protocolo', '=', 'P')],
    )

    item_com_st_ids = fields.One2many(
        comodel_name='sped.operacao.item',
        inverse_name='operacao_id',
        string='Item da operação fiscal',
        domain=[('tipo_protocolo', '=', 'S')]
    )
    item_simples_com_st_ids = fields.One2many(
        comodel_name='sped.operacao.item',
        inverse_name='operacao_id',
        string='Item da operação fiscal',
        domain=[('tipo_protocolo', '=', 'S')]
    )
