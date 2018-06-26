# -*- coding: utf-8 -*-
# Copyright 2018 ABGF
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, models, fields


class SpedEsocialTurnosTrabalho(models.Model):
    _name = "sped.esocial.turnos.trabalho"

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
        comodel_name='sped.transmissao',
    )
