# -*- coding: utf-8 -*-
# Copyright 2016 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
from datetime import datetime
from dateutil.relativedelta import relativedelta
from openerp import fields
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

        self.attach1 = self.env['ir.attachment'].create({
            'name': 'attach1.txt',
            'datas_fname': 'attach1.txt',
            'datas': base64.b64encode('world'),
        })

    def test_01_holiday_status_message(self):
        """ teste cenario 1: Atestado Medico
            Dias: -
            Mensagem: "Acima de 3 dias o atestado devera ser homologado na
            empresa de Medicina do Trabalho!"
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
            'attachment_ids': [(6, 0, [self.attach1.id])],
        })
        self.assertEqual(
            holiday_id.message,
            'Acima de 3 dias o atestado devera ser homologado na empresa de '
            'Medicina do Trabalho!',
            'hr_holidays: Mensagem invalida para holiday do Atestado Medico!')

    def test_02_holiday_status_message(self):
        """ teste cenário 2: Tratamento Dentario
            Dias: -
            Mensagem: "Acima de 3 dias o atestado devera ser homologado na
            empresa de Medicina do Trabalho!"
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
            'attachment_ids': [(6, 0, [self.attach1.id])],
        })
        self.assertEqual(
            holiday_id.message,
            'Acima de 3 dias o atestado devera ser homologado na empresa de '
            'Medicina do Trabalho!',
            'hr_holidays:Mensagem invalida no holiday do tratamento dentario!')

    def test_03_holiday_limit_days(self):
        """ teste do Holiday com holiday_status_id com limite de dias Corridos
            Limite de Dias: 5
        """
        holiday_status_id = self.env.ref(
            'l10n_br_hr_holiday.holiday_status_medical_certificate')
        self.hr_holidays.create({
            'name': '5 Dias Corridos',
            'holiday_type': 'employee',
            'holiday_status_id': holiday_status_id.id,
            'employee_id': self.employee_hruser_id.id,
            'date_from': fields.Datetime.from_string('2016-12-07 07:00:00'),
            'date_to':  fields.Datetime.from_string('2016-12-11 19:00:00'),
            'number_of_days_temp': 5,
            'attachment_ids': [(6, 0, [self.attach1.id])],
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
        self.hr_holidays.create({
            'name': '5 Dias Uteis',
            'holiday_type': 'employee',
            'holiday_status_id': holiday_status_id.id,
            'employee_id': self.employee_hruser_id.id,
            'date_from': fields.Datetime.from_string('2016-12-07 07:00:00'),
            'date_to':  fields.Datetime.from_string('2016-12-13 19:00:00'),
            'number_of_days_temp': 7,
            'attachment_ids': [(6, 0, [self.attach1.id])],
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
        self.hr_holidays.create({
            'name': 'Limite de 1 Hora de Compensação',
            'holiday_type': 'employee',
            'holiday_status_id': holiday_status_id.id,
            'employee_id': self.employee_hruser_id.id,
            'date_from': fields.Datetime.from_string('2016-12-07 07:00:00'),
            'date_to':  fields.Datetime.from_string('2016-12-07 08:00:00'),
            'number_of_days_temp': 1,
        })
        self.assertEqual(self.hr_holidays.search_count([
            ('employee_id', '=', self.employee_hruser_id.id)]), 1,
            'hr_holidays: Falha na criação do holiday com limite de 1 hora!')

    def test_06_holiday_attachements(self):
        """ teste do Holiday com obrigatoriedade de anexo
        """
        holiday_status_id = self.env.ref(
            'l10n_br_hr_holiday.holiday_status_paternity_leave')
        self.hr_holidays.create({
            'name': 'Licença Paternidade',
            'holiday_type': 'employee',
            'holiday_status_id': holiday_status_id.id,
            'employee_id': self.employee_hruser_id.id,
            'date_from': fields.Datetime.from_string('2016-12-07 07:00:00'),
            'date_to': fields.Datetime.from_string('2016-12-07 08:00:00'),
            'number_of_days_temp': 1,
            'attachment_ids': [(6, 0, [self.attach1.id])],
        })
        self.assertEqual(self.hr_holidays.search_count([
            ('employee_id', '=', self.employee_hruser_id.id)]), 1,
            'hr_holidays: Falha na criação do holiday com atestado!')
