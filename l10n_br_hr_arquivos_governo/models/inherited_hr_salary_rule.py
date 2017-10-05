# -*- coding: utf-8 -*-
# Copyright 2017 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from __future__ import division, print_function, unicode_literals

from openerp import models, fields


class HrSalaryRule(models.Model):
    _inherit = b"hr.salary.rule"

    codigo_darf = fields.Char(
        string=b"Código da DARF"
    )
