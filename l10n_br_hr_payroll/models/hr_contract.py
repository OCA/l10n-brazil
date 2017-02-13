# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models
from datetime import datetime


class HrContract(models.Model):

    _inherit = 'hr.contract'
    _rec_name = 'nome_contrato'

    @api.depends('employee_id', 'date_start')
    def _nome_contrato(self):
        for contrato in self:
            nome = contrato.employee_id.name
            inicio_contrato = contrato.date_start
            fim_contrato = contrato.date_end

            if inicio_contrato:
                inicio_contrato = datetime.strptime(inicio_contrato,
                                                    '%Y-%m-%d')
                inicio_contrato = inicio_contrato.strftime('%d/%m/%y')

            if fim_contrato:
                fim_contrato = datetime.strptime(fim_contrato, '%Y-%m-%d')
                fim_contrato = fim_contrato.strftime('%d/%m/%y')
                if fim_contrato > fields.Date.today():
                    fim_contrato = "- D. %s" % fim_contrato
                else:
                    fim_contrato = "- %s" % fim_contrato
            else:
                fim_contrato = ''
            matricula = contrato.name
            nome_contrato = '[%s] %s - %s %s' % (matricula,
                                                 nome, inicio_contrato,
                                                 fim_contrato)
            contrato.nome_contrato = nome_contrato

    nome_contrato = fields.Char(default="[mat] nome - inicio - fim",
                                compute="_nome_contrato", store=True)

    @api.multi
    def _buscar_salario_vigente_periodo(self, data_inicio, data_fim):
        contract_change_obj = self.env['l10n_br_hr.contract.change']
        change = contract_change_obj.search(
            [
                ('change_date', '>=', data_inicio),
                ('change_date', '<=', data_fim),
                ('wage', '>', 0),
            ],
            order="change_date DESC",
            limit=1,
        )
        return change.wage

    @api.multi
    def _salario_dia(self, data_inicio, data_fim):
        if data_inicio >= self.date_start and \
                (data_fim <= self.date_end or not self.date_end):
            return self.wage/30
        else:
            return self._buscar_salario_vigente_periodo(
                data_inicio, data_fim)/30

    @api.multi
    def _salario_hora(self, data_inicio, data_fim):
        if data_inicio >= self.date_start and \
                (data_fim <= self.date_end or not self.date_end):
            return self.wage/(
                220 if not self.monthly_hours else self.monthly_hours
            )
        else:
            return self._buscar_salario_vigente_periodo(
                data_inicio, data_fim)/(
                220 if not self.monthly_hours else self.monthly_hours
            )

    @api.multi
    def _salario_mes(self, data_inicio, data_fim):
        if data_inicio >= self.date_start and \
                (data_fim <= self.date_end or not self.date_end):
            return self.wage
        else:
            return self._buscar_salario_vigente_periodo(data_inicio, data_fim)

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
