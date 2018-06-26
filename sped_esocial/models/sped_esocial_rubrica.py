# -*- coding: utf-8 -*-
# Copyright 2017 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models


class SpedEsocialRubrica(models.Model):
    _name = 'sped.esocial.rubrica'
    _description = 'Tabela de Rubricas e-Social'
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
    rubrica_id = fields.Many2one(
        string='Rubricas',
        comodel_name='hr.salary.rule',
        required=True,
    )

    # S-1010 (Necessidade e Execução)
    requer_s1010 = fields.Boolean(
        string='Requer S-1010 neste Período',
        compute='_compute_requer_s1010',
        store=True,
    )
    sped_s1010 = fields.Boolean(
        string='Registro de Rubrica',
        compute='_compute_sped_s1010',
    )
    sped_s1010_registro = fields.Many2one(
        string='Registro S-1010',
        comodel_name='sped.transmissao',
    )
    situacao_s1010 = fields.Selection(
        string='Situação S-1010',
        selection=[
            ('1', 'Pendente'),
            ('2', 'Transmitida'),
            ('3', 'Erro(s)'),
            ('4', 'Sucesso'),
            ('5', 'Precisa Retificar'),
        ],
        related='sped_s1010_registro.situacao',
        readonly=True,
    )

    @api.depends('rubrica_id')
    def _compute_requer_s1010(self):
        for rubrica in self:
            requer_s1010 = False
            if not rubrica.sped_s1010 or \
                    rubrica.write_date > rubrica.sped_s1010_registro.data_hora_transmissao:
                requer_s1010 = True
            rubrica.requer_s1010 = requer_s1010

    @api.depends('rubrica_id', 'esocial_id')
    def _compute_nome(self):
        for rubrica in self:
            nome = ""
            if rubrica.rubrica_id:
                nome += rubrica.rubrica_id.name
            if rubrica.esocial_id.periodo_id:
                nome += ' (' + rubrica.esocial_id.periodo_id.name + ')'
            rubrica.nome = nome

    @api.depends('sped_s1010_registro')
    def _compute_sped_s1010(self):
        for rubrica in self:
            rubrica.sped_s1010 = True if rubrica.sped_s1010_registro else False
