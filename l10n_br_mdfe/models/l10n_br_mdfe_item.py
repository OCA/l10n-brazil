# -*- coding: utf-8 -*-
# Copyright 2018 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _
from odoo.addons.l10n_br_base.constante_tributaria import (
    MODELO_FISCAL,
    SITUACAO_NFE,
    MODELO_FISCAL_CFE,
    MODELO_FISCAL_NFE,
    SITUACAO_NFE_AUTORIZADA,
)


class L10nBrMdfeItem(models.Model):

    _name = 'l10n_br.mdfe.item'
    _description = 'Documento MDF-E Carga Item'
    # _rec_name = 'documento_chave',

    @api.depends('documento_chave')
    def _compute_dados(self):
        for record in self:
            if record.documento_chave:
                record.documento_modelo = record.documento_chave[20:22]
                record.documento_serie = record.documento_chave[23:25]
                record.documento_numero = record.documento_chave[26:35]

    def _compute_informacoes_documento(self):
        for record in self:
            if record.documento_id:
                volume_ids = record.documento_id.volume_ids
                quantidade = sum(line.quantidade for line in volume_ids)
                peso_liquido = sum(line.peso_liquido for line in volume_ids)
                peso_bruto = sum(line.peso_bruto for line in volume_ids)
                # volume_liquido = sum(record.documento_id.volume_ids.volume)
                # TODO: Taxa a ser configurada nas configuracões do módulo
                taxa = 0.1
                # volume = volume_liquido * (1 + taxa)
                record.update({
                    'quantidade': quantidade,
                    'peso_liquido': peso_liquido,
                    'peso_bruto': peso_bruto,
                    # 'volume_liquido': volume_liquido,
                })

    mdfe_id = fields.Many2one(
        comodel_name='sped.documento',
    )
    remetente_id = fields.Many2one(
        comodel_name='sped.participante',
        string='Remetente',
    )
    remetente_cidade_id = fields.Many2one(
        comodel_name='sped.municipio',
        string='Cidade remetente',
    )
    destinatario_id = fields.Many2one(
        comodel_name='sped.participante',
        string='Destinatario',
    )
    destinatario_cidade_id = fields.Many2one(
        comodel_name='sped.municipio',
        string='Cidade destinatário',
    )
    data_hora_solicitacao = fields.Datetime(
        string='Solicitação',
        default=lambda self: fields.Datetime.now(),
        readonly=True,
    )
    data_hora_carregamento = fields.Datetime()
    data_hora_expedicao = fields.Datetime()
    data_hora_entrega = fields.Datetime()
    observacoes = fields.Text()

    documento_id = fields.Many2one(
        comodel_name='sped.documento',
        domain=[('modelo', '=', [MODELO_FISCAL_NFE]), ('numero', '!=', 0),('cfop_id.codigo','not in',['5922','6922']),('situacao_nfe','=',SITUACAO_NFE_AUTORIZADA),
                '|',('item_referenciado_ids','=',False),('item_referenciado_ids.mdfe_id.situacao_mdfe','!=','autorizada')],
        string='NF-E/CT-E',
    )
    documento_chave = fields.Char(
        string='Chave',
        size=44,
        copy=False,

    )
    documento_modelo = fields.Selection(
        selection=MODELO_FISCAL,
        string='Modelo Fiscal',
        index=True,
        compute=_compute_dados,
    )
    documento_serie = fields.Char(
        string='Série',
        size=3,
        index=True,
        compute=_compute_dados,
    )
    documento_numero = fields.Float(
        string='Número',
        index=True,
        readonly=True,
        digits=(18, 0),
        compute=_compute_dados,
    )
    documento_situacao = fields.Selection(
        related='documento_id.situacao_nfe',
        selection=SITUACAO_NFE,
        string='Situação',
        readonly=True,
    )

    peso_liquido = fields.Float(
        compute='_compute_informacoes_documento',
        store=True,
    )
    peso_bruto = fields.Float(
        compute='_compute_informacoes_documento',
        store=True,
    )
    quantidade = fields.Float(
        compute='_compute_informacoes_documento',
        store=True,
    )
    volume_liquido = fields.Float(
        compute='_compute_informacoes_documento',
        store=True,
    )
    volume_bruto = fields.Float(
        compute='_compute_informacoes_documento',
        store=True,
    )

    @api.onchange('documento_chave')
    def _onchange_chave(self):
        if self.documento_chave:
            self.documento_id = self.documento_id.search(
                [('chave', '=', self.documento_chave)]
            )

    @api.onchange('documento_id')
    def _onchange_documento(self):

        if self.documento_id:
            self.documento_chave = self.documento_id.chave
            self.destinatario_cidade_id = self.documento_id.participante_municipio_id
            self.destinatario_id = self.documento_id.participante_id

            self.remetente_cidade_id = self.documento_id.empresa_id.municipio_id.id
            self.remetente_id = self.documento_id.empresa_id.participante_id.id
