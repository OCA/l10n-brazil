# -*- coding: utf-8 -*-
# Copyright (C) 2019 ABGF
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import api, fields, models, _


class HrPayrollType(models.Model):
    _name = "hr.payroll.type"
    _rec_name = 'description'

    name = fields.Char(
        string='Name',
    )

    description = fields.Char(
        string='Description',
    )
