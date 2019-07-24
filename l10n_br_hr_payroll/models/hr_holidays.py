# -*- coding: utf-8 -*-
# Copyright 2016 KMEE - Hendrix Costa <hendrix.costa@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields


class HrHolidays(models.Model):
    _inherit = 'hr.holidays'

    slip_ids = fields.One2many(
        comodel_name='hr.payslip',
        string=u'Holerites',
        inverse_name='holidays_ferias',
    )

    rubrica = fields.Char(
        string="Rubrica"
    )

    periodo = fields.Char(
        string="Data de afastamento"
    )

    valor_inss = fields.Float(
        string="Valor INSS"
    )
