# -*- coding: utf-8 -*-
# Copyright 2017 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models


class ResourceCalendarAttendance(models.Model):

    _inherit = 'resource.calendar.attendance'

    turno_id = fields.Many2one(
        string='Turno',
        comodel_name='esocial.turnos.trabalho'
    )
    hour_from = fields.Float(
        required=False,
    )
    hour_to = fields.Float(
        required=False,
    )
