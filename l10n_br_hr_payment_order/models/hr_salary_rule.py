# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields


class HrSalaryRule(models.Model):
    _inherit = "hr.salary.rule"

    eh_pagavel = fields.Boolean(
        string="É pagavel?"
    )
