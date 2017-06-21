# -*- coding: utf-8 -*-
# Copyright 2017 KMEE - Hendrix Costa <hendrix.costa@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import fields, models


class HrContract(models.Model):
    _inherit = 'hr.contract'

    weekly_hours = fields.Float(
        default=40,
    )
