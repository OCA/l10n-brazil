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
        self.hr_payroll_structure = self.env["hr.payroll.structure"]
        self.hr_payslip = self.env["hr.payslip"]
        self.hr_salary_rule = self.env["hr.salary.rule"]
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

    def test_cenario_01_rubrica_05(self):
        """
        DADO um funcionário com Função Comissionada
            E com Salário Base de R$ 10.936,46
        QUANDO tirar 10 dias de Férias
        ENTÃO o cálculo da Rubrica 5-Férias deve ser R$ 3.645,49
        """

        # ADD Ferias de 10 dias funcionario
        holiday_status_id = self.env.ref(
            'hr_holidays.holiday_status_cl')
        self.holiday_id = self.hr_holidays.create({
            'name': 'Ferias',
            'type': 'add',
            'holiday_type': 'employee',
            'holiday_status_id': holiday_status_id.id,
            'employee_id': self.employee_hr_user_id.id,
            'number_of_days_temp': 10,
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
            'employee_id': self.employee_hr_user_id.id,
            'date_from': fields.Datetime.from_string('2017-01-10 07:00:00'),
            'date_to': fields.Datetime.from_string('2017-01-20 17:00:00'),
            'number_of_days_temp': 10,
            'payroll_discount': True,
        })
        self.holiday_id.holidays_validate()

        # Rubrica
        self.hr_salary_rule_id = self.hr_salary_rule.create({
            'name': 'Rubrica de FERIAS',
            'sequence': '5',
            'code': 'REGRA_FERIAS',
            'category_id': self.env.ref('hr_payroll.BASIC').id,
            'condition_select': 'none',
            'amount_select': 'code',
            'amount_python_compute': 'result = worked_days.DIAS_BASE.'
                                     'number_of_days * contract.wage / 30',
        })

        # estrutura de salario
        self.hr_payroll_structure_id = self.hr_payroll_structure.create({
            'name': 'Estrutura de Salario',
            'parent_id': False,
            'code': 'FERIAS',
            'rule_ids': [(6, 0, [self.hr_salary_rule_id.id])]
        })

        # contrato do funcionario
        self.job_id = self.hr_job.create({'name': 'Cargo 1'})
        self.hr_contract_id = self.hr_contract.create({
            'name': 'Contrato Rubrica 05',
            'employee_id': self.employee_hr_user_id.id,
            'job_id': self.job_id.id,
            'type_id': self.env.ref('hr_contract.hr_contract_type_emp').id,
            'wage': 10936.46,
            'date_start': '2017-01-01',
            'working_hours': self.nacional_calendar_id.id,
            'struct_id': self.hr_payroll_structure_id.id,
        })

        # Criando a folha de pagamento
        date_from = '2017-01-01'
        date_to = '2017-01-31'
        employee_id = self.employee_hr_user_id.id,
        self.hr_payslip_id = self.hr_payslip.create({
            'employee_id': employee_id,
            'date_from': date_from,
            'date_to': date_to,
            'struct_id': self.hr_payroll_structure_id.id,
            'contract_id': self.hr_contract_id.id,
        })

        # Processando a folha de pagamento
        result = self.hr_payslip_id.onchange_employee_id(
            date_from, date_to, employee_id, self.hr_contract_id)
        worked_days_line_ids = []
        for line in result['value']['worked_days_line_ids']:
            worked_days_line_ids_obj = self.hr_payslip_worked_days.create({
                'name': line['name'],
                'sequence': line['sequence'],
                'code': line['code'],
                'number_of_days': line['number_of_days'],
                'number_of_hours': line['number_of_hours'],
                'contract_id': line['contract_id'],
                'payslip_id': self.hr_payslip_id.id,
            })
            worked_days_line_ids.append(worked_days_line_ids_obj)
        self.hr_payslip_id.compute_sheet()

        self.assertEqual(self.hr_payslip_id.line_ids.total, 10936.46,
                         'ERRO no Cálculo da rubrica 05 - FERIAS')
