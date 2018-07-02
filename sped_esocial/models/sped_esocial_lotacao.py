# -*- coding: utf-8 -*-
# Copyright 2017 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models


class SpedEsocialLotacao(models.Model):
    _name = 'sped.esocial.lotacao'
    _description = 'Tabela de Lotações Tributárias do e-Social'
    _rec_name = 'nome'
    _order = "nome"

    nome = fields.Char(
        string='Nome',
        compute='_compute_nome',
        store=True,
    )
    esocial_id = fields.Many2one(
        string='e-Social',
        comodel_name='sped.esocial',
        ondelete="cascade",
    )
    lotacao_id = fields.Many2one(
        string='Lotação',
        comodel_name='res.company',
        required=True,
    )

    # S-1020 (Necessidade e Execução)
    requer_s1020 = fields.Boolean(
        string='Requer S-1020 neste Período',
        compute='_compute_requer_s1020',
        store=True,
    )
    sped_s1020 = fields.Boolean(
        string='Registro de Estabelecimento',
        compute='_compute_sped_s1020',
    )
    sped_s1020_registro = fields.Many2one(
        string='Registro S-1020',
        comodel_name='sped.registro',
    )
    situacao_s1020 = fields.Selection(
        string='Situação S-1020',
        selection=[
            ('1', 'Pendente'),
            ('2', 'Transmitida'),
            ('3', 'Erro(s)'),
            ('4', 'Sucesso'),
            ('5', 'Precisa Retificar'),
        ],
        related='sped_s1020_registro.situacao',
        readonly=True,
    )

    @api.depends('lotacao_id')
    def _compute_requer_s1020(self):
        for lotacao in self:
            requer_s1020 = False
            if not lotacao.sped_s1020 or \
                    lotacao.write_date > lotacao.sped_s1020_registro.data_hora_transmissao:
                requer_s1020 = True
            lotacao.requer_s1020 = requer_s1020

    @api.depends('lotacao_id', 'esocial_id')
    def _compute_nome(self):
        for lotacao in self:
            nome = ""
            if lotacao.lotacao_id:
                nome += lotacao.lotacao_id.name
            if lotacao.esocial_id.periodo_id:
                nome += ' (' + lotacao.esocial_id.periodo_id.name + ')'
            lotacao.nome = nome

    @api.depends('sped_s1020_registro')
    def _compute_sped_s1020(self):
        for lotacao in self:
            lotacao.sped_s1020 = True if lotacao.sped_s1020_registro else False
