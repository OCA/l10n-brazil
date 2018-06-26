# -*- coding: utf-8 -*-
# Copyright 2017 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models


class SpedEsocialEstabelecimento(models.Model):
    _name = 'sped.esocial.estabelecimento'
    _description = 'Tabela de Estabelecimentos e-Social'
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
    estabelecimento_id = fields.Many2one(
        string='Estabelecimento',
        comodel_name='res.company',
        required=True,
    )

    # S-1005 (Necessidade e Execução)
    requer_s1005 = fields.Boolean(
        string='Requer S-1005 neste Período',
        compute='_compute_requer_s1005',
        store=True,
    )
    sped_s1005 = fields.Boolean(
        string='Registro de Estabelecimento',
        compute='_compute_sped_s1005',
    )
    sped_s1005_registro = fields.Many2one(
        string='Registro S-1005',
        comodel_name='sped.transmissao',
    )
    situacao_s1005 = fields.Selection(
        string='Situação S-1005',
        selection=[
            ('1', 'Pendente'),
            ('2', 'Transmitida'),
            ('3', 'Erro(s)'),
            ('4', 'Sucesso'),
            ('5', 'Precisa Retificar'),
        ],
        related='sped_s1005_registro.situacao',
        readonly=True,
    )

    @api.depends('estabelecimento_id')
    def _compute_requer_s1005(self):
        for estabelecimento in self:
            requer_s1005 = False
            if not estabelecimento.sped_s1005 or \
                    estabelecimento.write_date > estabelecimento.sped_s1005_registro.data_hora_transmissao:
                requer_s1005 = True
            estabelecimento.requer_s1005 = requer_s1005

    @api.depends('estabelecimento_id', 'esocial_id')
    def _compute_nome(self):
        for estabelecimento in self:
            nome = ""
            if estabelecimento.estabelecimento_id:
                nome += estabelecimento.estabelecimento_id.name
            if estabelecimento.esocial_id.periodo_id:
                nome += ' (' + estabelecimento.esocial_id.periodo_id.name + ')'
            estabelecimento.nome = nome

    @api.depends('sped_s1005_registro')
    def _compute_sped_s1005(self):
        for estabelecimento in self:
            estabelecimento.sped_s1005 = True if estabelecimento.sped_s1005_registro else False
