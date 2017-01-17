# -*- coding: utf-8 -*-
# Copyright 2016 KMEE - Hendrix Costa <hendrix.costa@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import fields
from openerp.tests import common


class TestHrPayslip(common.TransactionCase):

    def setUp(self):
        super(TestHrPayslip, self).setUp()
        # Usefull models
        self.res_users = self.env['res.users']
        self.hr_employee = self.env['hr.employee']
        self.resource_calendar = self.env['resource.calendar']
        self.hr_contract = self.env['hr.contract']
        self.hr_job = self.env['hr.job']
        self.hr_payslip = self.env["hr.payslip"]
        self.hr_payslip_worked_days = self.env['hr.payslip.worked_days']
        group_employee_id = self.ref('base.group_user')
        self.hr_holidays = self.env['hr.holidays']

        # Test users to use through the various tests
        self.user_hruser_id = self.res_users.create({
            'name': 'Hr User',
            'login': 'hruser',
            'alias_name': 'User Mileo',
            'email': 'hruser@email.com',
            'groups_id': [(6, 0, [group_employee_id])],
        })

        self.employee_hr_user_id = self.hr_employee.create({
            'name': 'Employee Luiza',
            'user_id': self.user_hruser_id.id,
        })
        # calendario padrao nacional
        self.nacional_calendar_id = self.resource_calendar.create({
            'name': 'Calendario Nacional',
            'country_id': self.env.ref("base.br").id,
        })

    def atribuir_ferias(self, quantidade_dias, date_from, date_to, employee_id):

        date_from = fields.Datetime.from_string(date_from)
        date_to = fields.Datetime.from_string(date_to)

        # Ferias aprovada pro funcionario
        holiday_status_id = self.env.ref(
            'hr_holidays.holiday_status_cl')
        self.holiday_id = self.hr_holidays.create({
            'name': 'Ferias',
            'type': 'add',
            'holiday_type': 'employee',
            'holiday_status_id': holiday_status_id.id,
            'employee_id': employee_id,
            'number_of_days_temp': quantidade_dias,
            'payroll_discount': True,
        })
        self.holiday_id.holidays_validate()

        # Funcionario goza das ferias
        holiday_status_id = self.env.ref(
            'hr_holidays.holiday_status_cl')
        self.holiday_id = self.hr_holidays.create({
            'name': 'Ferias',
            'holiday_type': 'employee',
            'type': 'remove',
            'holiday_status_id': holiday_status_id.id,
            'employee_id': employee_id,
            'date_from': date_from,
            'date_to': date_to,
            'number_of_days_temp': quantidade_dias,
            'payroll_discount': True,
        })
        self.holiday_id.holidays_validate()

    def criar_contrato(self, nome, wage, struct_id, employee_id):
        self.job_id = self.hr_job.create({'name': 'Função Comissionada'})
        hr_contract_id = self.hr_contract.create({
            'name': nome,
            'employee_id': employee_id,
            'job_id': self.job_id.id,
            'type_id': self.env.ref('hr_contract.hr_contract_type_emp').id,
            'wage': wage,
            'date_start': '2017-01-01',
            'working_hours': self.nacional_calendar_id.id,
            'struct_id': struct_id,
        })
        return hr_contract_id

    def criar_folha_pagamento(self, date_from, date_to, contract_id, employee_id):
        hr_payslip_id = self.hr_payslip.create({
            'employee_id': employee_id,
            'date_from': date_from,
            'date_to': date_to,
            # 'struct_id': self.hr_payroll_structure_id.id,
            'contract_id': contract_id,
        })
        return hr_payslip_id

    def processar_folha_pagamento(self, hr_payslip):
        # Processando a folha de pagamento
        result = hr_payslip.onchange_employee_id(
            hr_payslip.date_from, hr_payslip.date_to, hr_payslip.employee_id.id,
            hr_payslip.contract_id)
        worked_days_line_ids = []
        for line in result['value']['worked_days_line_ids']:
            worked_days_line_ids_obj = self.hr_payslip_worked_days.create({
                'name': line['name'],
                'sequence': line['sequence'],
                'code': line['code'],
                'number_of_days': line['number_of_days'],
                'number_of_hours': line['number_of_hours'],
                'contract_id': line['contract_id'],
                'payslip_id': hr_payslip.id,
            })
            worked_days_line_ids.append(worked_days_line_ids_obj)
        hr_payslip.compute_sheet()

    def test_cenario_01_rubrica_05(self):
        """DADO um funcionário com Função Comissionada
        E com Salário Base de R$ 10.936,46
        QUANDO tirar 10 dias de Férias
        ENTÃO o cálculo da Rubrica 5-Férias deve ser R$ 3.645,49
        """
        employee_id = self.employee_hr_user_id.id
        date_from = '2017-01-10 07:00:00'
        date_to = '2017-01-20 17:00:00'
        # estrutura de salario
        hr_payroll_structure_id = self.env.ref(
            'l10n_br_hr_payroll.hr_salary_structure_FERIAS').id

        self.atribuir_ferias(10, date_from, date_to, employee_id)

        hr_contract_id = self.criar_contrato(
            'Contrato Ferias', 10936.46, hr_payroll_structure_id, employee_id)

        hr_payslip = self.criar_folha_pagamento(
            '2017-01-01', '2017-01-31', hr_contract_id.id, employee_id)

        self.processar_folha_pagamento(hr_payslip)

        self.assertEqual(hr_payslip.line_ids[0].total, 3645.49,
                         'ERRO no Cálculo da rubrica 05 - FERIAS')

    def test_cenario_02_rubrica_05(self):
        """DADO um funcionário com Função Comissionada
        E com Salário Base de R$ 10.936,46
        QUANDO tirar 10 dias de Férias
        ENTÃO o cálculo da Rubrica 10-Abono 1/3 Férias deve ser R$ 1.215,16
        """
        employee_id = self.employee_hr_user_id.id
        date_from = '2017-01-10 07:00:00'
        date_to = '2017-01-20 17:00:00'
        # estrutura de salario
        hr_payroll_structure_id = self.env.ref(
            'l10n_br_hr_payroll.hr_salary_structure_FERIAS').id

        self.atribuir_ferias(10, date_from, date_to, employee_id)

        hr_contract_id = self.criar_contrato(
            'Contrato Ferias', 10936.46, hr_payroll_structure_id, employee_id)

        hr_payslip = self.criar_folha_pagamento(
            '2017-01-01', '2017-01-31', hr_contract_id.id, employee_id)

        self.processar_folha_pagamento(hr_payslip)

        self.assertEqual(hr_payslip.line_ids[1].total, 1215.16,
                         'ERRO no Cálculo da rubrica 05 - 1/3 FERIAS')
