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
        self.resource_leaves = self.env['resource.calendar.leaves']
        self.resource_calendar = self.env['resource.calendar']

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
        # create feriado para calendario nacional
        self.holiday_nacional_01 = self.resource_leaves.create({
            'name': 'Feriado em Janeiro 01',
            'date_from': fields.Datetime.from_string('2017-01-08 00:00:00'),
            'date_to': fields.Datetime.from_string('2017-01-08 23:59:59'),
            'calendar_id': self.nacional_calendar_id.id,
            'leave_type': 'F',
            'abrangencia': 'N',
        })
        self.resource_leaves.create({
            'name': 'Feriado em Janeiro 02',
            'date_from': fields.Datetime.from_string('2017-03-18 00:00:00'),
            'date_to': fields.Datetime.from_string('2017-03-18 23:59:59'),
            'calendar_id': self.nacional_calendar_id.id,
            'leave_type': 'F',
            'abrangencia': 'N',
        })

    def criar_falta_nao_remunerada(self):
        # create falta funcionario
        holiday_status_id = self.env.ref(
            'l10n_br_hr_holiday.holiday_status_unjustified_absence')
        holiday_id = self.hr_holidays.create({
            'name': 'Falta Injusticada',
            'holiday_type': 'employee',
            'holiday_status_id': holiday_status_id.id,
            'employee_id': self.employee_hr_user_id.id,
            'date_from': fields.Datetime.from_string('2017-01-10 07:00:00'),
            'date_to': fields.Datetime.from_string('2017-01-10 17:00:00'),
            'number_of_days_temp': 1,
            'payroll_discount': True,
        })
        holiday_id.holidays_validate()

    def test_01_get_quantity_discount_DSR(self):
        """ teste cenario 01: Obter DSR para desconto da folha de pagamento,
        sabendo que o feriado (DSR) é no domingo.
        """
        date_from = '2017-01-01 00:00:01'
        date_to = '2017-01-31 23:59:59'
        self.criar_falta_nao_remunerada()

        leaves = self.env['hr.holidays'].get_ocurrences(
            self.employee_hr_user_id.id, date_from, date_to)

        quantity_DSR_discount = self.resource_calendar.\
            get_quantity_discount_DSR(leaves['faltas_nao_remuneradas'],
                                      self.nacional_calendar_id.leave_ids,
                                      date_from, date_to)

        self.assertEqual(quantity_DSR_discount, 1,
                         'ERRO no Cálculo de Desconto de DSR apartir de '
                         'falta na semana e feriado no domingo(Perder 1 DSR).')

    def test_02_get_quantity_discount_DSR(self):
        """ teste cenario 02: Obter DSR para desconto da folha de pagamento,
        sabendo que o feriado (DSR) é na sexta feira, isto é, se o funcionario
        faltar, perderá o DSR do domingo e do feriado.
        """
        # create feriado para calendario nacional na sexta feira
        self.holiday_nacional_01 = self.resource_leaves.create({
            'name': 'Feriado na sexta de Janeiro',
            'date_from': fields.Datetime.from_string('2017-01-13 00:00:00'),
            'date_to': fields.Datetime.from_string('2017-01-13 23:59:59'),
            'calendar_id': self.nacional_calendar_id.id,
            'leave_type': 'F',
            'abrangencia': 'N',
        })
        self.criar_falta_nao_remunerada()

        date_from = '2017-01-01 00:00:01'
        date_to = '2017-01-31 23:59:59'
        leaves = self.env['hr.holidays'].get_ocurrences(
            self.employee_hr_user_id.id, date_from, date_to)
        quantity_DSR_discount = self.resource_calendar.\
            get_quantity_discount_DSR(leaves['faltas_nao_remuneradas'],
                                      self.nacional_calendar_id.leave_ids,
                                      date_from, date_to)

        self.assertEqual(quantity_DSR_discount, 2,
                         'ERRO: Cálculo de Desconto de DSR apartir de falta'
                         ' na semana e feriado em dia de semana. '
                         '(Perder 2 DSRs).')

    def test_03_quantidade_DSR_em_intervalo(self):
        """ teste cenario 03: Obter quantidade de DSR em determinado intervalo
        """
        # teste intervalo sem feriados e com 5 domingos no mês
        date_from = '2017-01-01 00:00:01'
        date_to = '2017-01-31 23:59:59'
        quantity_DSR = self.nacional_calendar_id.quantidade_de_DSR(date_from,
                                                                   date_to)
        self.assertEqual(quantity_DSR, 5,
                         'ERRO: Cálculo de quantidade de DSR em determinado '
                         'intervalo Inválido')

        # teste intervalo que contem um feriado em dia de semana + 4 domingos
        date_from = '2017-03-01 00:00:01'
        date_to = '2017-03-31 23:59:59'
        quantity_DSR = self.nacional_calendar_id.quantidade_de_DSR(date_from,
                                                                   date_to)
        self.assertEqual(quantity_DSR, 5,
                         'ERRO: Cálculo de quantidade de DSR em determinado '
                         'intervalo com feriados no mês Invalido!')

    # def test_04_quantidade_dias_ferias(self):
    #     """ teste função  quantidade_dias_ferias: Obter a quantidade de dias
    #     que o funcionario ficou de férias em um determinado período
    #     """
    #     date_from = '2017-01-10 07:00:00'
    #     date_to = '2017-01-20 17:00:00'
    #
    #     # Ferias aprovada pro funcionario
    #     holiday_status_id = self.env.ref(
    #         'l10n_br_hr_holiday.holiday_status_vacation')
    #     self.holiday_id = self.hr_holidays.create({
    #         'name': 'Ferias',
    #         'type': 'add',
    #         'holiday_type': 'employee',
    #         'holiday_status_id': holiday_status_id.id,
    #         'employee_id': self.employee_hr_user_id.id,
    #         'number_of_days_temp': 10,
    #         'payroll_discount': True,
    #     })
    #     self.holiday_id.holidays_validate()
    #
    #     # Funcionario goza das ferias
    #     holiday_status_id = self.env.ref(
    #         'l10n_br_hr_holiday.holiday_status_vacation')
    #     self.holiday_id = self.hr_holidays.create({
    #         'name': 'Ferias',
    #         'holiday_type': 'employee',
    #         'type': 'remove',
    #         'holiday_status_id': holiday_status_id.id,
    #         'employee_id': self.employee_hr_user_id.id,
    #         'date_from': date_from,
    #         'date_to': date_to,
    #         'number_of_days_temp': 10,
    #         'payroll_discount': True,
    #     })
    #     self.holiday_id.holidays_validate()
    #
    #     qtd_dias_ferias = self.resource_calendar.get_quantidade_dias_ferias(
    #         self.employee_hr_user_id.id, date_from, date_to
    #     )
    #     self.assertEqual(qtd_dias_ferias, 10,
    #                      'ERRO: Cálculo de quantidade de DIAS de Férias!')
