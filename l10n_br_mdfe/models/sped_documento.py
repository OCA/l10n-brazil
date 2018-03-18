# -*- coding: utf-8 -*-
# Copyright 2018 KMEE INFORMATICA LTDA, Grupo Zenir
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from __future__ import division, print_function, unicode_literals

from odoo import api, fields, models, _
from odoo.addons.l10n_br_base.constante_tributaria import (
    MODELO_FISCAL_MDFE,
    TIPO_TRANSPORTADOR,
    MODALIDADE_TRANSPORTE,
    TIPO_EMITENTE,
    TIPO_RODADO,
    TIPO_CARROCERIA
)


class SpedDocumento(models.Model):

    _inherit = 'sped.documento'

    @api.depends('modelo', 'emissao', 'importado_xml', 'situacao_nfe')
    def _compute_permite_alteracao(self):
        super(SpedDocumento, self)._compute_permite_alteracao()

        for documento in self:
            if not documento.modelo == MODELO_FISCAL_MDFE:
                super(SpedDocumento, documento)._compute_permite_alteracao()
                continue

            documento.permite_alteracao = True

    # def _check_permite_alteracao(self, operacao='create', dados={},
    #                              campos_proibidos=[]):
    #
    #     CAMPOS_PERMITIDOS = [
    #         'message_follower_ids',
    #         'justificativa',
    #         'chave_cancelamento',
    #     ]
    #     for documento in self:
    #         if documento.modelo != MODELO_FISCAL_CFE:
    #             super(SpedDocumento, documento)._check_permite_alteracao(
    #                 operacao,
    #                 dados,
    #             )
    #             continue
    #
    #         if documento.emissao != TIPO_EMISSAO_PROPRIA:
    #             super(SpedDocumento, documento)._check_permite_alteracao(
    #                 operacao,
    #                 dados,
    #             )
    #             continue
    #
    #         if documento.permite_alteracao:
    #             continue
    #
    #         permite_alteracao = False
    #
    #         if documento.situacao_nfe == SITUACAO_NFE_AUTORIZADA:
    #             for campo in dados:
    #                 if campo in CAMPOS_PERMITIDOS:
    #                     permite_alteracao = True
    #                     break
    #                 elif campo not in campos_proibidos:
    #                     campos_proibidos.append(campo)
    #
    #         if permite_alteracao:
    #             continue

    tipo_emitente = fields.Selection(
        selection=TIPO_EMITENTE,
        string='Tipo de emitente',
    )
    tipo_transportador = fields.Selection(
        selection=TIPO_TRANSPORTADOR,
        string='Tipo do transportador'
    )
    modalidade_transporte = fields.Selection(
        selection=MODALIDADE_TRANSPORTE,
        string='Modalidade',
    )
    veiculo_id = fields.Many2one(
        string='Veiculo',
        comodel_name='sped.veiculo',
    )
    veiculo_rntrc = fields.Char(
        string='RNTRC',
        size=20,
        related='veiculo_id.rntrc',
        store=True,
    )
    veiculo_placa = fields.Char(
        string='Placa',
        size=8,
        related='veiculo_id.placa',
        store=True,
    )
    veiculo_estado_id = fields.Many2one(
        comodel_name='sped.estado',
        string='Estado',
        related='veiculo_id.estado_id',
        store=True,
    )
    veiculo_ciot = fields.Char(
        string='Tipo CIOT',
        help='Também Conhecido como conta frete',
        related='veiculo_id.ciot',
        store=True,
    )
    veiculo_tipo_rodado = fields.Selection(
        selection=TIPO_RODADO,
        string='Rodado',
        related='veiculo_id.tipo_rodado',
        store=True,
    )
    veiculo_tipo_carroceria = fields.Selection(
        selection=TIPO_CARROCERIA,
        string='Tipo de carroceria',
        related='veiculo_id.tipo_carroceria',
        store=True,
    )
    veiculo_tara_kg = fields.Float(
        string='Tara (kg)',
        related = 'veiculo_id.tara_kg',
        store = True,
    )
    veiculo_capacidade_kg = fields.Float(
        string='Capacidade (kg)',
        related='veiculo_id.capacidade_kg',
        store=True,
    )
    veiculo_capacidade_m3 = fields.Float(
        string='Capacidade (m³)',
        related='veiculo_id.capacidade_m3',
        store=True,
    )
    carregamento_municipio_ids = fields.Many2many(
        comodel_name='sped.municipio',
        string='Municípios carregamento',
        help='Máximo 50',
    )
    percurso_estado_ids = fields.Many2many(
        comodel_name='sped.estado',
        string='UFs de percurso',
        help='Máximo 25',
    )
    descarregamento_estado_id = fields.Many2one(
        comodel_name='sped.estado',
        string='Estado descarregamento'
    )
    condutor_ids = fields.One2many(
        comodel_name='l10n_br.mdfe.condutor',
        inverse_name='documento_id',
    )
    lacre_ids = fields.One2many(
        comodel_name='l10n_br.mdfe.lacre',
        inverse_name='documento_id',
    )
    seguro_ids = fields.One2many(
        comodel_name='l10n_br.mdfe.seguro',
        inverse_name='documento_id',
    )
    item_mdfe_ids = fields.One2many(
        comodel_name='l10n_br.mdfe.item',
        inverse_name='mdfe_id',
    )

    @api.onchange('operacao_id', 'emissao', 'natureza_operacao_id')
    def _onchange_operacao_id(self):
        result = super(SpedDocumento, self)._onchange_operacao_id()

        if self.operacao_id.modelo == MODELO_FISCAL_MDFE:
            result['value']['tipo_emitente'] = self.operacao_id.tipo_emitente
            result['value']['tipo_transportador'] = \
                self.operacao_id.tipo_transportador
            result['value']['modalidade_transporte'] = \
                self.operacao_id.modalidade_transporte

        return result
