# -*- coding: utf-8 -*-
# Copyright 2016 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import datetime
from dateutil.relativedelta import relativedelta

from openerp.tests import common


class TestHrHoliday(common.TransactionCase):

    def setUp(self):
        super(TestHrHoliday, self).setUp()

        # Usefull models
        self.res_users = self.env['res.users']
        self.hr_employee = self.env['hr.employee']
        self.hr_holidays = self.env['hr.holidays']

        # Test users to use through the various tests
        self.user_hruser_id = self.res_users.create({
            'name': 'Hr User',
            'login': 'hruser',
            'alias_name': 'User Mileo',
            'email': 'hruser@email.com',
        })

        self.employee_hruser_id = self.hr_employee.create({
            'name': 'Employee Luiza',
            'user_id': self.user_hruser_id.id,
        })

    def test_01_holiday_status_message(self):
        """ teste cenario 1: Atestado Medico
            Dias: -
            Mensagem: "Above 3 days, the certificate must be approved by
            the company of Occupational Medicine!"
        """
        holiday_status_id = self.env.ref(
            'l10n_br_hr_holiday.holiday_status_medical_certificate')
        holiday_id = self.hr_holidays.create({
            'name': 'Atestado medico',
            'holiday_type': 'employee',
            'holiday_status_id': holiday_status_id.id,
            'employee_id': self.employee_hruser_id.id,
            'date_from': (datetime.today() - relativedelta(days=1)),
            'date_to': datetime.today(),
            'number_of_days_temp': 1,
        })
        self.assertEqual(
            holiday_id.message,
            'Above 3 days, the certificate must be approved by the company of '
            'Occupational Medicine!',
            'hr_holidays: Mensagem invalida para holiday do Atestado Medico!')

    def test_02_holiday_status_message(self):
        """ teste cenário 2: Tratamento Dentario
            Dias: -
            Mensagem: "Above 3 days, the certificate must be approved by
            the company of Occupational Medicine!"
        """
        holiday_status_id = self.env.ref(
            'l10n_br_hr_holiday.holiday_status_dental_treatment')
        holiday_id = self.hr_holidays.create({
            'name': 'Tratamento Dentario',
            'holiday_type': 'employee',
            'holiday_status_id': holiday_status_id.id,
            'employee_id': self.employee_hruser_id.id,
            'date_from': (datetime.today() - relativedelta(days=1)),
            'date_to': datetime.today(),
            'number_of_days_temp': 1,
        })
        self.assertEqual(
            holiday_id.message,
            'Above 3 days, the certificate must be approved by the company of'
            ' Occupational Medicine!',
            'hr_holidays:Mensagem invalida no holiday do tratamento dentario!')

    def test_03_holiday_limit_days(self):
        """ teste do Holiday com holiday_status_id com limite de dias Corridos
            Limite de Dias: 5
        """
        holiday_status_id = self.env.ref(
            'l10n_br_hr_holiday.holiday_status_medical_certificate')
        holiday_id = self.hr_holidays.create({
            'name': '5 Dias Corridos',
            'holiday_type': 'employee',
            'holiday_status_id': holiday_status_id.id,
            'employee_id': self.employee_hruser_id.id,
            'date_from': datetime.strptime('07-12-2016 07:00:00',
                                           "%d-%m-%Y %H:%M:%S"),
            'date_to':  datetime.strptime('11-12-2016 19:00:00',
                                          "%d-%m-%Y %H:%M:%S"),
            'number_of_days_temp': 5,
        })
        self.assertEqual(self.hr_holidays.search_count([
            ('employee_id', '=', self.employee_hruser_id.id)]), 1,
            'hr_holidays: Falha na criação do holiday com limite de 5 '
            'dias corridos!')

    def test_04_holiday_limit_days(self):
        """ teste do Holiday com holiday_status_id com limite de dias Uteis
            Limite de Dias: 5
        """
        holiday_status_id = self.env.ref(
            'l10n_br_hr_holiday.holiday_status_Legal_adoption')
        holiday_id = self.hr_holidays.create({
            'name': '5 Dias Uteis',
            'holiday_type': 'employee',
            'holiday_status_id': holiday_status_id.id,
            'employee_id': self.employee_hruser_id.id,
            'date_from': datetime.strptime('07-12-2016 07:00:00',
                                           "%d-%m-%Y %H:%M:%S"),
            'date_to':  datetime.strptime('13-12-2016 19:00:00',
                                          "%d-%m-%Y %H:%M:%S"),
            'number_of_days_temp': 7,
        })
        self.assertEqual(self.hr_holidays.search_count(
            [('employee_id', '=', self.employee_hruser_id.id)]), 1,
            'hr_holidays: Falha na criação do holiday limite de 5 dias Uteis!')

    def test_05_holiday_limit_hours(self):
        """ teste do Holiday com holiday_status_id com limite de Horas
            Limite de Horas: 1
        """
        holiday_status_id = self.env.ref(
            'l10n_br_hr_holiday.holiday_status_compensation_1hour')
        holiday_id = self.hr_holidays.create({
            'name': 'Limite de 1 Hora de Compensação',
            'holiday_type': 'employee',
            'holiday_status_id': holiday_status_id.id,
            'employee_id': self.employee_hruser_id.id,
            'date_from': datetime.strptime('07-12-2016 07:00:00',
                                           "%d-%m-%Y %H:%M:%S"),
            'date_to':  datetime.strptime('07-12-2016 08:00:00',
                                          "%d-%m-%Y %H:%M:%S"),
            'number_of_days_temp': 1,
        })
        self.assertEqual(self.hr_holidays.search_count([
            ('employee_id', '=', self.employee_hruser_id.id)]), 1,
            'hr_holidays: Falha na criação do holiday com limite de 1 hora!')
