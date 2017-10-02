# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia -
#   Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from __future__ import division, print_function, unicode_literals

from odoo import api, fields, models


class SpedProduto(models.Model):
    _inherit = 'sped.produto'

    ncm_id = fields.Many2one(
        comodel_name='sped.ncm',
        string='NCM')
    cest_ids = fields.Many2many(
        comodel_name='sped.cest',
        related='ncm_id.cest_ids',
        string='Códigos CEST',
    )
    exige_cest = fields.Boolean(
        string='Exige código CEST?',
        compute='_compute_exige_cest',
    )
    cest_id = fields.Many2one(
        comodel_name='sped.cest',
        string='CEST'
    )
    protocolo_id = fields.Many2one(
        comodel_name='sped.protocolo.icms',
        string='Protocolo/Convênio',
    )
    al_ipi_id = fields.Many2one(
        comodel_name='sped.aliquota.ipi',
        string='Alíquota de IPI',
    )
    al_pis_cofins_id = fields.Many2one(
        comodel_name='sped.aliquota.pis.cofins',
        string='Alíquota de PIS e COFINS',
    )
    servico_id = fields.Many2one(
        comodel_name='sped.servico',
        string='Código do serviço',
    )
    nbs_id = fields.Many2one(
        comodel_name='sped.nbs',
        string='NBS',
    )
    unidade_tributacao_ncm_id = fields.Many2one(
        comodel_name='sped.unidade',
        related='ncm_id.unidade_id',
        string='Unidade de tributação do NCM',
        readonly=True,
    )
    fator_conversao_unidade_tributacao_ncm = fields.Float(
        string='Fator de conversão entre as unidades',
        default=1,
    )
    exige_fator_conversao_unidade_tributacao_ncm = fields.Boolean(
        string='Exige fator de conversão entre as unidades?',
        compute='_compute_exige_fator_conversao_ncm',
    )

    @api.depends('ncm_id', 'unidade_id')
    def _compute_exige_fator_conversao_ncm(self):
        for produto in self:
            if produto.unidade_id and produto.unidade_tributacao_ncm_id:
                produto.exige_fator_conversao_unidade_tributacao_ncm = (
                    produto.unidade_id.id !=
                    produto.unidade_tributacao_ncm_id.id
                )
            else:
                produto.exige_fator_conversao_unidade_tributacao_ncm = False
                produto.fator_conversao_unidade_tributacao_ncm = 1

    def _ajusta_cest(self):
        for produto in self:
            if not produto.ncm_id:
                produto.exige_cest = False
                produto.cest_id = False
                continue

            if len(produto.ncm_id.cest_ids) == 0:
                produto.exige_cest = False
                produto.cest_id = False
                continue

            produto.exige_cest = True

            if len(produto.ncm_id.cest_ids) == 1:
                produto.cest_id = produto.ncm_id.cest_ids[0].id

    @api.depends('ncm_id')
    def _compute_exige_cest(self):
        self._ajusta_cest()

    @api.onchange('ncm_id')
    def onchange_ncm(self):
        self._ajusta_cest()
