# -*- coding: utf-8 -*-
# Copyright 2018 ABGF
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, models, fields


class SpedEsocialTurnosTrabalho(models.Model):
    _name = "sped.esocial.turnos.trabalho"

    name = fields.Char(
        related='sped_esocial_turnos_trabalho_id.name'
    )

    esocial_id = fields.Many2one(
        string="e-Social",
        comodel_name="sped.esocial",
        required=True,
    )
    sped_esocial_turnos_trabalho_id = fields.Many2one(
        string="Turno de Trabalho",
        comodel_name="esocial.turnos.trabalho",
        required=True,
    )
    sped_s1050_registro = fields.Many2one(
        string='Registro S-1050',
        comodel_name='sped.registro',
    )
    situacao_s1050 = fields.Selection(
        string="Situação S-1050",
        selection=[
            ('1', 'Pendente'),
            ('2', 'Transmitida'),
            ('3', 'Erro(s)'),
            ('4', 'Sucesso'),
            ('5', 'Precisa Retificar'),
        ],
        related="sped_s1050_registro.situacao",
        readonly=True,
    )
