# -*- coding: utf-8 -*-
# Copyright 2017 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models
from datetime import datetime


class SpedEfdReinfServico(models.Model):
    _name = 'sped.efdreinf.servico'
    _description = 'Serviços de NFs de Eventos Periódicos EFD/Reinf'
    _rec_name = 'nome'
    _order = "nome"

    nome = fields.Char(
        string='Nome',
        compute='_compute_nome',
        store=True,
    )
    efdreinf_nfs_id = fields.Many2one(
        string='NF',
        comodel_name='sped.efdreinf.nfs',
    )
    produto_id = fields.Many2one(
        string='Produto',
        comodel_name='product.product',
        related='servico_nfs_id.product_id',
        store=True,
    )
    servico_nfs_id = fields.Many2one(
        string='Serviço',
        comodel_name='account.invoice.line',
    )
    tp_servico_id = fields.Many2one(
        string='Tipo de Serviço',
        comodel_name='sped.classificacao_servico',
        related='produto_id.tp_servico_id',
    )
    vr_base_ret = fields.Float(
        string='Base para Retenção',
        digits=[14, 2],
    )
    vr_retencao = fields.Float(
        string='Valor da Retenção',
        digits=[14, 2],
    )
    vr_ret_sub = fields.Float(
        string='Retenção Subcontratada',
        digits=[14, 2],
    )
    vr_nret_princ = fields.Float(
        string='Vr.não Retido por Ação',
        digits=[14, 2],
    )
    vr_servicos_15 = fields.Float(
        string='Vr.Serviços 15 anos',
        digits=[14, 2],
    )
    vr_servicos_20 = fields.Float(
        string='Vr.Serviços 20 anos',
        digits=[14, 2],
    )
    vr_servicos_25 = fields.Float(
        string='Vr.Serviços 25 anos',
        digits=[14, 2],
    )
    vr_adicional = fields.Float(
        string='Vr.Adicional por Aposent.Especial',
        digits=[14, 2],
    )
    vr_nret_adic = fields.Float(
        string='Vr.Ret. não efetuada ou dep.em juízo',
        digitss=[14, 2],
    )

    @api.depends('efdreinf_nfs_id')
    def _compute_nome(self):
        for servico in self:
            nf = servico.efdreinf_nfs_id.num_docto or ''
            produto = servico.servico_nfs_id.name or ''
            valor = servico.servico_nfs_id.price_total or 0
            nome = nf
            nome += ' (' + produto + ')'
            nome += ' R$ ' + '{:20,.2f}'.format(valor)
