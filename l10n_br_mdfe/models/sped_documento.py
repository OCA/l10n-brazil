# -*- coding: utf-8 -*-
# Copyright 2018 KMEE INFORMATICA LTDA, Grupo Zenir
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

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
    # veiculo_codigo = fields.Char(
    #     string='Código veiculo',
    # )
    veiculo_rntrc = fields.Char(
        related='veiculo_id.rntrc',
        size=20,
        readonly=True,
    )
    veiculo_ciot = fields.Char(
        string='Tipo CIOT',
        help='Também Conhecido como conta frete',
    )
    veiculo_placa = fields.Char(
        string='Placa',
        size=8,
        related='veiculo_id.placa',
    )
    veiculo_estado_id = fields.Many2one(
        comodel_name='sped.estado',
        string='Estado',
    )
    veiculo_tipo_rodado = fields.Selection(
        selection=TIPO_RODADO,
        string='Rodado',
    )
    veiculo_tipo_carroceria = fields.Selection(
        selection=TIPO_CARROCERIA,
        string='Tipo de carroceria',
    )
    veiculo_tara_kg = fields.Float(
        string='Tara (kg)'
    )
    veiculo_capacidade_kg = fields.Float(
        string='Capacidade (kg)',
    )
    veiculo_capacidade_m3 = fields.Float(
        string='Capacidade (m³)'
    )
    condutor_id = fields.Many2one(
        comodel_name='sped.participante',
        string='Condutor',
        # domain=[('eh_pessoa_fisica', '=', True)]
    )
    condutor_nome = fields.Char(
        related='condutor_id.nome',
        readonly=True,
        string='Nome completo',
    )
    condutor_cfp = fields.Char(
        related='condutor_id.cnpj_cpf',
        readonly=True,
        string='CPF',
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
