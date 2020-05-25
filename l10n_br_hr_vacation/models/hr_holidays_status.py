# -*- coding: utf-8 -*-
# Copyright 2019 ABGF - Hendrix Costa <hendrix.costa@abgf.gov.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, models, fields


class HrHolidaysStatus(models.Model):
    _inherit = 'hr.holidays.status'

    descontar_ferias = fields.Boolean(
        string=u'Descontar férias?',
        help=u'Descontar dias de férias quando ultrapassar 5 dias de faltas?',
        default=False,
    )
