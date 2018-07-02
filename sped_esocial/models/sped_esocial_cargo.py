# -*- coding: utf-8 -*-
# Copyright 2017 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models


class SpedEsocialCargo(models.Model):
    _name = 'sped.esocial.cargo'
    _description = 'Tabela de Cargos e-Social'
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
    cargo_id = fields.Many2one(
        string='Cargos',
        comodel_name='hr.job',
        required=True,
    )

    # S-1030 (Necessidade e Execução)
    requer_s1030 = fields.Boolean(
        string='Requer S-1030 neste Período',
        compute='_compute_requer_s1030',
        store=True,
    )
    sped_s1030 = fields.Boolean(
        string='Registro de Cargo',
        compute='_compute_sped_s1030',
    )
    sped_s1030_registro = fields.Many2one(
        string='Registro S-1030',
        comodel_name='sped.registro',
    )
    situacao_s1030 = fields.Selection(
        string='Situação S-1030',
        selection=[
            ('1', 'Pendente'),
            ('2', 'Transmitida'),
            ('3', 'Erro(s)'),
            ('4', 'Sucesso'),
            ('5', 'Precisa Retificar'),
        ],
        related='sped_s1030_registro.situacao',
        readonly=True,
    )

    @api.depends('cargo_id')
    def _compute_requer_s1030(self):
        for cargo in self:
            requer_s1030 = False
            if not cargo.sped_s1030 or \
                    cargo.write_date > cargo.sped_s1030_registro.data_hora_transmissao:
                requer_s1030 = True
            cargo.requer_s1030 = requer_s1030

    @api.depends('cargo_id', 'esocial_id')
    def _compute_nome(self):
        for cargo in self:
            nome = ""
            if cargo.cargo_id:
                nome += cargo.cargo_id.name
            if cargo.esocial_id.periodo_id:
                nome += ' (' + cargo.esocial_id.periodo_id.name + ')'
            cargo.nome = nome

    @api.depends('sped_s1030_registro')
    def _compute_sped_s1030(self):
        for cargo in self:
            cargo.sped_s1030 = True if cargo.sped_s1030_registro else False
