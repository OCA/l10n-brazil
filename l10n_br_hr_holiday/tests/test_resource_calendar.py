# -*- coding: utf-8 -*-
# Copyright 2016 KMEE - Hendrix Costa <hendrix.costa@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import fields
from openerp.tests import common


class TestHrHoliday(common.TransactionCase):

    def setUp(self):
        super(TestHrHoliday, self).setUp()
        # Usefull models
        self.resource_calendar = self.env['resource.calendar']
        self.res_users = self.env['res.users']
        self.hr_employee = self.env['hr.employee']

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

        self.employee_hruser_id = self.hr_employee.create({
            'name': 'Employee Luiza',
            'user_id': self.user_hruser_id.id,
        })

    def test_01_get_ocurrences(self):
        """ teste da funcao que obtem as faltas de determinado funcionario
        """
        # create an ocurrence
        holiday_status_id = self.env.ref(
            'l10n_br_hr_holiday.holiday_status_unjustified_absence')
        holiday_id = self.hr_holidays.create({
            'name': 'Falta Injusticada',
            'holiday_type': 'employee',
            'holiday_status_id': holiday_status_id.id,
            'employee_id': self.employee_hruser_id.id,
            'date_from': fields.Datetime.from_string('2017-01-10 07:00:00'),
            'date_to': fields.Datetime.from_string('2017-01-10 17:00:00'),
            'number_of_days_temp': 1,
            'payroll_discount': True,
        })
        holiday_id.holidays_validate()

        data_inicio = '2017-01-01 00:00:01'
        data_final = '2017-01-31 23:59:59'

        faltas = self.resource_calendar.get_ocurrences(
            self.employee_hruser_id.id, data_inicio, data_final)
        quantidade_faltas = faltas['quantidade_dias_faltas_nao_remuneradas']

        self.assertEqual(
            quantidade_faltas, 1,
            'ERRO: Nao foi possivel obter faltas do Funcionario!')
        self.assertEqual(
            faltas['faltas_nao_remuneradas'][0].name, u'Falta Injusticada',
            'ERRO: Nao foi possivel obter faltas do Funcionario!')

    def test_02_get_ocurrences(self):
        """ teste da funcao que obtem a quantidade de faltas de determinado
        funcionario. Faltas de varios dias seguidos

        """
        # create an ocurrence
        holiday_status_id = self.env.ref(
            'l10n_br_hr_holiday.holiday_status_unjustified_absence')
        holiday_id = self.hr_holidays.create({
            'name': 'Falta Injusticada de 3 dias',
            'holiday_type': 'employee',
            'holiday_status_id': holiday_status_id.id,
            'employee_id': self.employee_hruser_id.id,
            'date_from': fields.Datetime.from_string('2017-01-10 07:00:00'),
            'date_to': fields.Datetime.from_string('2017-01-12 17:00:00'),
            'number_of_days_temp': 3,
            'payroll_discount': True,
        })
        holiday_id.holidays_validate()

        data_inicio = '2017-01-01 00:00:01'
        data_final = '2017-01-31 23:59:59'

        faltas = self.resource_calendar.get_ocurrences(
            self.employee_hruser_id.id, data_inicio, data_final)
        quantidade_faltas = faltas['quantidade_dias_faltas_nao_remuneradas']

        self.assertEqual(
            quantidade_faltas, 3,
            'ERRO: Nao foi possivel obter faltas do Funcionario!')
        self.assertEqual(
            faltas['faltas_nao_remuneradas'][0].name,
            u'Falta Injusticada de 3 dias',
            'ERRO: Nao foi possivel obter faltas do Funcionario!')
