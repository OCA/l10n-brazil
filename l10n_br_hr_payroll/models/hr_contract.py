# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models


class HrContract(models.Model):

    _inherit = 'hr.contract'

    @api.multi
    def _salario_dia(self, data_inicio, data_fim):
        if data_inicio >= self.date_start and data_fim <= self.date_end:
            return self.wage/30

    @api.multi
    def _salario_hora(self, data_inicio, data_fim):
        if data_inicio >= self.date_start and data_fim <= self.date_end:
            return self.wage/(
                220 if not self.monthly_hours else self.monthly_hours
            )

    @api.multi
    def _salario_mes(self, data_inicio, data_fim):
        if data_inicio >= self.date_start and data_fim <= self.date_end:
            return self.wage

    specific_rule_ids = fields.One2many(
        comodel_name='hr.contract.salary.rule',
        inverse_name='contract_id',
        string=u"Rúbricas específicas",
    )
    change_salary_ids = fields.One2many(
        comodel_name='l10n_br_hr.contract.change',
        inverse_name='contract_id',
        string=u"Remuneração",
        domain=[
            ('change_type', '=', 'remuneracao')
        ],
    )
    change_workdays_ids = fields.One2many(
        comodel_name='l10n_br_hr.contract.change',
        inverse_name='contract_id',
        string=u"Jornada",
        domain=[
            ('change_type', '=', 'jornada')
        ],
    )
    change_job_ids = fields.One2many(
        comodel_name='l10n_br_hr.contract.change',
        inverse_name='contract_id',
        string=u"Atividade/Cargo",
        domain=[
            ('change_type', '=', 'cargo-atividade')
        ],
    )
    change_labor_union_ids = fields.One2many(
        comodel_name='l10n_br_hr.contract.change',
        inverse_name='contract_id',
        string=u"Filiação Sindical",
        domain=[
            ('change_type', '=', 'filiacao-sindical')
        ],
    )
    change_place_ids = fields.One2many(
        comodel_name='l10n_br_hr.contract.change',
        inverse_name='contract_id',
        string=u"Lotação/Local de trabalho",
        domain=[
            ('change_type', '=', 'filiacao-sindical')
        ],
    )
