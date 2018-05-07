# -*- coding: utf-8 -*-
# Copyright 2018
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields


class HrRamal(models.Model):
    _name = 'hr.ramal'

    name = fields.Char(
        string=u'Nº Ramal',
        required=True,
    )

    hr_employee_ids = fields.One2many(
        comodel_name='hr.employee',
        inverse_name='ramais',
        string=u'Funcionários',
    )
