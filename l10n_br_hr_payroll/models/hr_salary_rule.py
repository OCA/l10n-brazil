# -*- coding: utf-8 -*-
# Copyright (C) 2016 KMEE (http://www.kmee.com.br)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import api, fields, models


class HrSalaryRule(models.Model):
    _inherit = 'hr.salary.rule'

    compoe_base_INSS = fields.Boolean(
        string=u'Compõe Base INSS'
    )

    compoe_base_IR = fields.Boolean(
        string=u'Compõe Base IR'
    )

    compoe_base_FGTS = fields.Boolean(
        string=u'Compõe Base FGTS'
    )
