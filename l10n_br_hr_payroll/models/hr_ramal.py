# -*- coding: utf-8 -*-
# Copyright 2018
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, models, fields
from openerp.exceptions import ValidationError


class HrRamal(models.Model):
    _name = 'hr.ramal'

    @api.constrains('name')
    def _check_description(self):
        if len(self.search([('name', '=', self.name)]).ids) > 1:
            raise ValidationError(
                "Este ramal já está cadastrado!"
            )

    name = fields.Char(
        string=u'Nº Ramal',
        required=True,
    )

    hr_employee_ids = fields.One2many(
        comodel_name='hr.employee',
        inverse_name='ramais',
        string=u'Funcionários',
    )
