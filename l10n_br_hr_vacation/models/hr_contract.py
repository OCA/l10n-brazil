# -*- coding: utf-8 -*-
# Copyright 2016 KMEE - Hendrix Costa <hendrix.costa@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields


class HrContract(models.Model):
    _inherit = 'hr.contract'

    holidays_ids = fields.One2many(
        comodel_name='hr.holidays',
        inverse_name='contract_id',
        string='Periodos Aquisitivos Alocados'
    )
