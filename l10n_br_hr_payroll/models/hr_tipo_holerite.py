# -*- coding: utf-8 -*-
# Copyright 2018
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api
from openerp.addons.l10n_br_hr_payroll.models.hr_payslip import TIPO_DE_FOLHA


class HrRamal(models.Model):
    _name = 'hr.tipo.holerite'

    _sql_constraints = [
        ('tipo_holerite_unico',
         'unique(tipo_holerite)',
         'Este Tipo de Holerite já existe!')
    ]

    name = fields.Char(
        string='Nome',
        compute='_get_tipo_holerite_name'
    )

    tipo_holerite = fields.Selection(
        string=u'Tipo de Holerite',
        selection=TIPO_DE_FOLHA,
    )

    specif_salary_rule_id = fields.Many2many(
        string=u'Funcionário',
        comodel_name='hr.contract.salary.rule',
        relation='specif_salary_rule_tipo_holerite_rel',
        column1='salary_rule_id',
        column2='tipo_holerite_id',
    )

    @api.multi
    def _get_tipo_holerite_name(self):
        for record in self:
            record.name = record.tipo_holerite
