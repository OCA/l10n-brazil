# -*- coding: utf-8 -*-
# Copyright 2017 KMEE Hendrix Costa
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import fields, models


class HrPayslip(models.Model):

    _inherit = 'hr.payslip'

    periodo_aquisitivo_provisao = fields.Char(
        string=u'Período Aquisitivo do Calculo',
        readonly=True,
        help=u'Campo apenas para informação do período aquisitivo',
    )
