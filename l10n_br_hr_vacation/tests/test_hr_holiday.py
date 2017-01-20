# -*- coding: utf-8 -*-
# Copyright 2016 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import fields
from openerp.tests import common


class TestHrHoliday(common.TransactionCase):

    def setUp(self):
        super(TestHrHoliday, self).setUp()

        # Usefull models
        self.res_users = self.env['res.users']
        self.hr_employee = self.env['hr.employee']
        self.hr_holidays = self.env['hr.holidays']
        self.hr_contract = self.env['hr.contract']
        self.hr_job = self.env['hr.job']

        self.user_hr_user_id = self.res_users.create({
            'name': 'Hr User',
            'login': 'hruser',
            'alias_name': 'User Mileo',
            'email': 'hruser@email.com',
        })

        self.employee_hruser_id = self.hr_employee.create({
            'name': 'Employee Luiza',
            'user_id': self.user_hr_user_id.id,
        })

        self.job_id = self.hr_job.create({'name': 'Funcionario'})
        self.hr_contract.create({
            'name': "Contrato Test do funcionario",
            'employee_id': self.employee_hruser_id.id,
            'job_id': self.job_id.id,
            'type_id': self.env.ref('hr_contract.hr_contract_type_emp').id,
            'wage': 2000.00,
            'date_start': '2016-01-01',
            'struct_id': self.env.ref('hr_payroll.structure_base').id
        })

    def test_01_atribuicao_ferias(self):
        """
        O modulo tem um croon que uma vez por dia dispara uma função que
        verifica todos os funcionarios que tem mais de 1 ano de trabalho
        a partir da data de contratacao ou da data das ultimas ferias.
        Caso tenha mais de um ano, alocar férias de 30 dias ao funcionario
        """

        # Disparando a funcao manualmente
        self.employee_hruser_id.function_vacation_verify()

        domain = [('employee_id', '=', self.employee_hruser_id.id)]
        holidays_ids = self.hr_holidays.search(domain)

        self.assertEquals(len(holidays_ids), 1)
        self.assertEquals(holidays_ids.number_of_days_temp, 30)
        self.assertEquals(holidays_ids.type, 'add')

    def test_02_atribuicao_ferias_02(self):
        """
        Validar se executar a funcao mais de uma vez, sera criado apenas uma
        ferias para cada funcionario
        """
        # Disparando a funcao manualmente 2 vezes
        self.employee_hruser_id.function_vacation_verify()
        self.employee_hruser_id.function_vacation_verify()

        domain = [('employee_id', '=', self.employee_hruser_id.id)]
        holidays_ids = self.hr_holidays.search(domain)

        self.assertEquals(len(holidays_ids), 1)
        self.assertEquals(holidays_ids.number_of_days_temp, 30)
        self.assertEquals(holidays_ids.type, 'add')

    def test_03_solicitacao_ferias(self):
        """
        Funcionário cria um pedido de férias de 20 dias e 10 dias
        de abono pecuniario
        """
        # Atribuindo Férias automaticamente
        self.employee_hruser_id.function_vacation_verify()
        domain = [('employee_id', '=', self.employee_hruser_id.id)]
        periodo_aquisitivo = self.hr_holidays.search(domain)
        # aprovação da alocação de férias
        periodo_aquisitivo.holidays_validate()

        # Solicitacao de férias do funcionario
        holiday_status_id = self.env.ref(
            'l10n_br_hr_vacation.holiday_status_vacation')
        ferias = self.hr_holidays.create({
            'name': 'Ferias Do  HrUser',
            'type': 'remove',
            'parent_id': periodo_aquisitivo.id,
            'holiday_type': 'employee',
            'holiday_status_id': holiday_status_id.id,
            'employee_id': self.employee_hruser_id.id,
            'vacations_days': 20,
            'sold_vacations_days': 10,
            'number_of_days_temp': 30,
            'date_from': fields.Datetime.from_string('2017-12-10 07:00:00'),
            'date_to': fields.Datetime.from_string('2017-12-30 19:00:00')
        })
        # Aprovacao da solicitacao do funcionario
        ferias.holidays_validate()

        domain = [
            ('employee_id', '=', self.employee_hruser_id.id),
            ('type', '=', 'remove'),
            ('state', '=', 'validate')
        ]
        holidays_ids = self.hr_holidays.search(domain)

        self.assertEquals(holidays_ids.type, 'remove')
        self.assertEquals(len(holidays_ids), 1)
        self.assertEquals(holidays_ids.number_of_days_temp, 30)
        self.assertEquals(holidays_ids.sold_vacations_days, 10)
        self.assertEquals(holidays_ids.vacations_days, 20)
