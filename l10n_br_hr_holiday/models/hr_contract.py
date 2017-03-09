# -*- coding: utf-8 -*-
# Copyright 2016 KMEE - Hendrix Costa <hendrix.costa@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import fields, models


class HrContract(models.Model):
    _inherit = 'hr.contract'

    hr_holiday_ids = fields.One2many(
        comodel_name='hr.holidays',
        inverse_name='contrato_id',
        string='Abonos de faltas'
    )
