# -*- coding: utf-8 -*-
# Copyright 2016 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

# from openerp import fields
from openerp.tests import common
# from openerp.exceptions import Warning as UserError


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
        # self.hr_contract.create({
        #     'name': "Contrato Test do funcionario",
        #     'employee_id': self.employee_hruser_id.id,
        #     'job_id': self.job_id.id,
        #     'type_id': self.env.ref('hr_contract.hr_contract_type_emp').id,
        #     'wage': 2000.00,
        #     'date_start': '2017-01-01',
        #     'struct_id': self.env.ref('hr_payroll.structure_base').id
        # })

        self.holiday_status_id = self.env.ref(
            'l10n_br_hr_vacation.holiday_status_vacation')

    # def atribuir_ferias(self, employee_id):
    #     """
    #     Executa a função de verificação e alocação de férias
    #     :return: Holidays: Holidays tipo ADD que aloca 30 dias de férias ao
    #     funcionario.
    #     """
    #     # Disparando a funcao manualmente
    #     self.employee_hruser_id.function_vacation_verify()
    #     # recuperando as férias alocadas
    #     domain = [('employee_id', '=', employee_id)]
    #     holidays_ids = self.hr_holidays.search(domain)
    #     holidays_ids.holidays_validate()
    #     return holidays_ids

    def test_00(self):
        pass
    # def test_01_atribuicao_ferias(self):
    #     """
    #     O modulo tem um croon que uma vez por dia dispara uma função que
    #     verifica todos os funcionarios que tem mais de 1 ano de trabalho
    #     a partir da data de contratacao ou da data das ultimas ferias.
    #     Caso tenha mais de um ano, alocar férias de 30 dias ao funcionario
    #     """
    #     holidays_ids = self.atribuir_ferias(self.employee_hruser_id.id)
    #
    #     self.assertEquals(len(holidays_ids), 1)
    #     self.assertEquals(holidays_ids.number_of_days_temp, 30)
    #     self.assertEquals(holidays_ids.type, 'add')

    # def test_02_atribuicao_ferias_02(self):
    #     """
    #     Validar se executar a funcao mais de uma vez, sera criado apenas uma
    #     ferias para cada funcionario
    #     """
    #     # Disparando a funcao manualmente 2 vezes
    #     holidays_ids = self.atribuir_ferias(self.employee_hruser_id.id)
    #     holidays_ids = self.atribuir_ferias(self.employee_hruser_id.id)
    #
    #     self.assertEquals(len(holidays_ids), 1)
    #     self.assertEquals(holidays_ids.number_of_days_temp, 30)
    #     self.assertEquals(holidays_ids.type, 'add')

    # def test_03_solicitacao_ferias(self):
    #     """
    #     Funcionário cria um pedido de férias de 20 dias e 10 dias
    #     de abono pecuniario
    #     """
    #     # Atribuindo Férias
    #     periodo_aquisitivo = self.atribuir_ferias(self.employee_hruser_id.id)
    #
    #     # Solicitacao de férias do funcionario
    #     ferias = self.hr_holidays.create({
    #         'name': 'Ferias Do  HrUser',
    #         'type': 'remove',
    #         'parent_id': periodo_aquisitivo.id,
    #         'holiday_type': 'employee',
    #         'holiday_status_id': self.holiday_status_id.id,
    #         'employee_id': self.employee_hruser_id.id,
    #         'vacations_days': 20,
    #         'sold_vacations_days': 10,
    #         'number_of_days_temp': 30,
    #         'date_from': fields.Datetime.from_string('2017-12-10 07:00:00'),
    #         'date_to': fields.Datetime.from_string('2017-12-30 19:00:00')
    #     })
    #     # Aprovacao da solicitacao do funcionario
    #     ferias.holidays_validate()
    #
    #     domain = [
    #         ('employee_id', '=', self.employee_hruser_id.id),
    #         ('type', '=', 'remove'),
    #         ('state', '=', 'validate')
    #     ]
    #     holidays_ids = self.hr_holidays.search(domain)
    #
    #     self.assertEquals(holidays_ids.type, 'remove')
    #     self.assertEquals(len(holidays_ids), 1)
    #     self.assertEquals(holidays_ids.number_of_days_temp, 30)
    #     self.assertEquals(holidays_ids.sold_vacations_days, 10)
    #     self.assertEquals(holidays_ids.vacations_days, 20)

    # def test_04_limite_abono(self):
    #     """
    #     Limite de 10 dias de abono pecuniario.
    #     Disparar Raise se o Funcionário tenta criar um pedido de férias
    #     de 19 dias de ferias e 11 dias de abono pecuniario.
    #     """
    #     # Atribuindo Férias
    #     periodo_aquisitivo = self.atribuir_ferias(self.employee_hruser_id.id)
    #
    #     with self.assertRaises(UserError):
    #         self.hr_holidays.create({
    #             'name': 'Ferias Do  HrUser',
    #             'type': 'remove',
    #             'parent_id': periodo_aquisitivo.id,
    #             'holiday_type': 'employee',
    #             'holiday_status_id': self.holiday_status_id.id,
    #             'employee_id': self.employee_hruser_id.id,
    #             'vacations_days': 19,
    #             'sold_vacations_days': 11,
    #             'number_of_days_temp': 30,
    #             'date_from':
        # fields.Datetime.from_string('2017-12-10 07:00:0'),
    #             'date_to': fields.Datetime.from_string('2017-12-28 19:00:00')
    #         })

    # def test_05_limite_minimo_ferias(self):
    #     """
    #     Limite de no mínimo 10 dias de Férias por período selecionado.
    #     Disparar Raise se o Funcionário tenta criar um pedido de férias com
    #     menos de 10 dias.
    #     """
    #     # Atribuindo Férias
    #     periodo_aquisitivo = self.atribuir_ferias(self.employee_hruser_id.id)
    #
    #     with self.assertRaises(UserError):
    #         self.hr_holidays.create({
    #             'name': 'Ferias Do  HrUser',
    #             'type': 'remove',
    #             'parent_id': periodo_aquisitivo.id,
    #             'holiday_type': 'employee',
    #             'holiday_status_id': self.holiday_status_id.id,
    #             'employee_id': self.employee_hruser_id.id,
    #             'vacations_days': 9,
    #             'sold_vacations_days': 10,
    #             'number_of_days_temp': 19,
    #             'date_from':
        # fields.Datetime.from_string('2017-12-10 07:00:0'),
    #             'date_to': fields.Datetime.from_string('2017-12-19 19:00:00')
    #         })

    # def test_06_limite_dias_periodo_aquisitivo(self):
    #     """
    #     Limite de dias selecionados de acordo com o período
    #     aquisitivo selecionado.
    #     """
    #     # Atribuindo Férias de 30 dias
    #     periodo_aquisitivo = self.atribuir_ferias(self.employee_hruser_id.id)
    #
    #     with self.assertRaises(UserError):
    #         self.hr_holidays.create({
    #             'name': 'Ferias Do  HrUser',
    #             'type': 'remove',
    #             'parent_id': periodo_aquisitivo.id,
    #             'holiday_type': 'employee',
    #             'holiday_status_id': self.holiday_status_id.id,
    #             'employee_id': self.employee_hruser_id.id,
    #             'vacations_days': 21,
    #             'sold_vacations_days': 10,
    #             'number_of_days_temp': 31,
    #             'date_from':
        # fields.Datetime.from_string('2017-01-01 07:00:0'),
    #             'date_to':
        # fields.Datetime.from_string('2017-01-21 19:00:00'),
    #         })

    # def test_07_divisao_ferias(self):
    #     """
    #     Permitir que o funcionario, faça 2 solicitações de férias, dividindo
    #     assim as suas férias em 2 períodos diferentes.
    #     """
    #     # Atribuindo Férias de 30 dias
    #     periodo_aquisitivo = self.atribuir_ferias(self.employee_hruser_id.id)
    #
    #     self.hr_holidays.create({
    #         'name': 'Ferias Do  HrUser 1',
    #         'type': 'remove',
    #         'parent_id': periodo_aquisitivo.id,
    #         'holiday_type': 'employee',
    #         'holiday_status_id': self.holiday_status_id.id,
    #         'employee_id': self.employee_hruser_id.id,
    #         'vacations_days': 10,
    #         'sold_vacations_days': 5,
    #         'number_of_days_temp': 15,
    #         'date_from': fields.Datetime.from_string('2017-01-01 07:00:00'),
    #         'date_to': fields.Datetime.from_string('2017-01-10 19:00:00'),
    #     })
    #
    #     self.hr_holidays.create({
    #         'name': 'Ferias Do  HrUser 2',
    #         'type': 'remove',
    #         'parent_id': periodo_aquisitivo.id,
    #         'holiday_type': 'employee',
    #         'holiday_status_id': self.holiday_status_id.id,
    #         'employee_id': self.employee_hruser_id.id,
    #         'vacations_days': 10,
    #         'sold_vacations_days': 5,
    #         'number_of_days_temp': 15,
    #         'date_from': fields.Datetime.from_string('2017-12-01 07:00:00'),
    #         'date_to': fields.Datetime.from_string('2017-12-10 19:00:00'),
    #     })
    #
    #     domain = [
    #         ('employee_id', '=', self.employee_hruser_id.id),
    #         ('type', '=', 'remove'),
    #     ]
    #     holidays_ids = self.hr_holidays.search(domain)
    #
    #     self.assertEquals(len(holidays_ids), 2)
    #     self.assertEquals(
    #         sum(holidays_ids.mapped('number_of_days_temp') or [0.0]), 30)

    # def test_08_limite_dias_periodo_aquisitivo(self):
    #     """
    #     Limitar solicitações de usuário para que somadas as solicitações de
    #     férias, nao ultrapasse os dias dísponiveis.
    #     """
    #     # Atribuindo Férias de 30 dias
    #     periodo_aquisitivo = self.atribuir_ferias(self.employee_hruser_id.id)
    #
    #     self.hr_holidays.create({
    #         'name': 'Ferias Do  HrUser 1',
    #         'type': 'remove',
    #         'parent_id': periodo_aquisitivo.id,
    #         'holiday_type': 'employee',
    #         'holiday_status_id': self.holiday_status_id.id,
    #         'employee_id': self.employee_hruser_id.id,
    #         'vacations_days': 10,
    #         'sold_vacations_days': 5,
    #         'number_of_days_temp': 15,
    #         'date_from': fields.Datetime.from_string('2017-01-01 07:00:00'),
    #         'date_to': fields.Datetime.from_string('2017-01-10 19:00:00'),
    #     })
    #
    #     with self.assertRaises(UserError):
    #         self.hr_holidays.create({
    #             'name': 'Ferias Do  HrUser 2',
    #             'type': 'remove',
    #             'parent_id': periodo_aquisitivo.id,
    #             'holiday_type': 'employee',
    #             'holiday_status_id': self.holiday_status_id.id,
    #             'employee_id': self.employee_hruser_id.id,
    #             'vacations_days': 11,
    #             'sold_vacations_days': 5,
    #             'number_of_days_temp': 16,
    #             'date_from':
        # fields.Datetime.from_string('2017-08-01 07:00:0'),
    #             'date_to':
        # fields.Datetime.from_string('2017-08-10 19:00:00'),
    #         })

    # def test_09_limite_dias_periodo_aquisitivo(self):
    #     """
    #     Limitar solicitações de usuário para que somadas as solicitações de
    #     fériasnao ultrapasse o limite de dias (10) para abono pecuniario
    #     """
    #     # Atribuindo Férias de 30 dias
    #     periodo_aquisitivo = self.atribuir_ferias(self.employee_hruser_id.id)
    #
    #     self.hr_holidays.create({
    #         'name': 'Ferias Do  HrUser 1',
    #         'type': 'remove',
    #         'parent_id': periodo_aquisitivo.id,
    #         'holiday_type': 'employee',
    #         'holiday_status_id': self.holiday_status_id.id,
    #         'employee_id': self.employee_hruser_id.id,
    #         'vacations_days': 10,
    #         'sold_vacations_days': 5,
    #         'number_of_days_temp': 15,
    #         'date_from': fields.Datetime.from_string('2017-01-01 07:00:00'),
    #         'date_to': fields.Datetime.from_string('2017-01-10 19:00:00'),
    #     })
    #
    #     with self.assertRaises(UserError):
    #         self.hr_holidays.create({
    #             'name': 'Ferias Do  HrUser 2',
    #             'type': 'remove',
    #             'parent_id': periodo_aquisitivo.id,
    #             'holiday_type': 'employee',
    #             'holiday_status_id': self.holiday_status_id.id,
    #             'employee_id': self.employee_hruser_id.id,
    #             'vacations_days': 9,
    #             'sold_vacations_days': 6,
    #             'number_of_days_temp': 15,
    #             'date_from':
        # fields.Datetime.from_string('2017-08-01 07:00:0'),
    #             'date_to':
        # fields.Datetime.from_string('2017-08-09 19:00:00'),
    #         })
