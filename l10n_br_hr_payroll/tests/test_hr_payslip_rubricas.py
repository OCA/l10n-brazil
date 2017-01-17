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
        self.hr_payroll_structure = self.env["hr.payroll.structure"]
        self.hr_payslip_worked_days = self.env['hr.payslip.worked_days']
        group_employee_id = self.ref('base.group_user')
        self.hr_holidays = self.env['hr.holidays']

        # Test users to use through the various tests
        self.user_hr_user_id = self.res_users.create({
            'name': 'Hr User',
            'login': 'hruser',
            'alias_name': 'User Mileo',
            'email': 'hruser@email.com',
            'groups_id': [(6, 0, [group_employee_id])],
        })

        self.employee_hr_user_id = self.hr_employee.create({
            'name': 'Employee Luiza',
            'user_id': self.user_hr_user_id.id,
        })
        # calendario padrao nacional
        self.nacional_calendar_id = self.resource_calendar.create({
            'name': 'Calendario Nacional',
            'country_id': self.env.ref("base.br").id,
        })

    def atribuir_ferias(self, quantidade_dias, date_from, date_to,
                        employee_id):

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

    def criar_folha_pagamento(self, date_from, date_to, contract_id,
                              employee_id):
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
            hr_payslip.date_from, hr_payslip.date_to,
            hr_payslip.employee_id.id, hr_payslip.contract_id)
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

    def criar_estrutura_salario(self, name, code, rule_id):
        hr_payroll_structure_id = self.hr_payroll_structure.create({
            'name': name,
            'parent_id': False,
            'code': code,
            'rule_ids': [(6, 0, [rule_id])]
        })
        return hr_payroll_structure_id

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

    def test_cenario_02(self):
        """Rubrica 10 - Abono 1/3 Férias - Variação 1
        DADO um funcionário com Função Comissionada
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

    def test_cenario_03(self):
        """
        Rubrica 42 - Abono Pecuniario Férias - Variação 1
        DADO um funcionário com Função Comissionada
        E com Salário Base de R$ 10.936,46
        QUANDO tirar 10 dias de Abono Pecuniário
        ENTÃO o cálculo da Rubrica 42-Abono Pecuniário Férias
        deve ser R$ 3.645,49
        """
        pass

    def test_cenario_04(self):
        """
        Rubrica 47 - 1/3 Abono Pecuniário - Variação 1
        DADO um funcionário com Função Comissional
        E com Salário Base de R$ 10.936,46
        QUANDO tirar 10 dias de Abono Pecuniário
        ENTÃO o cálculo da Rubrica 47-1/3 Abono Pecuniário
        deve ser R$ 1.215,16
        """
        pass

    def test_cenario_05(self):
        """
        Rubrica 397 - Honorário Presidente
        DADO um funcionário com Função Presidente
        E com Salário Base de R$ 8.447,07
        QUANTO trabalhar 30 dias
        ENTÃO o cálculo da Rubrica 397-Honorário Presidente
        deve ser R$ 8.447,07
        """
        pass

    def test_cenario_17(self):
        """Rubrica 502 - Reembolso Auxílio Creche/Babá - Variação 1
        DADO um funcionário com Reembolso Auxílio Creche/Baba de R$ 370,71
        E com Salário Base de R$ 10.936,46
        QUANDO trabalhar por 20 dias
        ENTÃO o cálculo da Rubrica502-Reembolso Auxílio Creche/Babá deve ser R$ 370,71
        """
        pass

    def test_cenario_36(self):
        """
        Rubrica 5 - Férias - Variação 2
        DADO um funcionário com Função Comissionada
        E com Salário Base de R$ 29.483,08
        QUANDO tira 9 dias de Férias no mês
        ENTÃO o cálculo da Rubrica 5-Férias deve ser R$ 8.844,92
        """
        employee_id = self.employee_hr_user_id.id
        date_from = '2017-01-20 07:00:00'
        date_to = '2017-01-28 17:00:00'

        hr_payroll_structure_id = self.env.ref(
            'l10n_br_hr_payroll.hr_salary_structure_FERIAS').id

        self.atribuir_ferias(9, date_from, date_to, employee_id)

        hr_contract_id = self.criar_contrato(
            'Contrato Ferias', 29483.08, hr_payroll_structure_id, employee_id)

        hr_payslip = self.criar_folha_pagamento(
            '2017-01-01', '2017-01-31', hr_contract_id.id, employee_id)

        self.processar_folha_pagamento(hr_payslip)

        self.assertEqual(hr_payslip.line_ids[0].total, 8844.92,
                         'ERRO no Cálculo da rubrica 05 - FERIAS')

    def test_cenario_37(self):
        """
        Rubrica 5 - Férias - Variação 3
        DADO um funcionário com Função Comissionada
        E com Salário Base de R$ 10.936,46
        QUANDO tira 20 dias de Férias no mês
        ENTÃO o cálculo da Rubrica 5-Férias deve ser R$ 7.290,97
        """
        employee_id = self.employee_hr_user_id.id
        date_from = '2017-01-01 07:00:00'
        date_to = '2017-01-20 17:00:00'

        hr_payroll_structure_id = self.env.ref(
            'l10n_br_hr_payroll.hr_salary_structure_FERIAS').id

        self.atribuir_ferias(20, date_from, date_to, employee_id)

        hr_contract_id = self.criar_contrato(
            'Contrato Ferias', 10936.46, hr_payroll_structure_id, employee_id)

        hr_payslip = self.criar_folha_pagamento(
            '2017-01-01', '2017-01-31', hr_contract_id.id, employee_id)

        self.processar_folha_pagamento(hr_payslip)

        self.assertEqual(hr_payslip.line_ids[0].total, 7290.97,
                         'ERRO no Cálculo da rubrica 05 - FERIAS')

    def test_cenario_38(self):
        """
        Rubrica 5 - Férias - Variação 4
        DADO um funcionário com Função Comissionada
        E com Salário Base de R$ 10.936,46
        QUANDO tira 12 dias de Férias no mês
        ENTÃO o cálculo da Rubrica 5-Férias deve ser R$ 4.374,58
        """
        employee_id = self.employee_hr_user_id.id
        date_from = '2017-01-10 07:00:00'
        date_to = '2017-01-21 17:00:00'

        hr_payroll_structure_id = self.env.ref(
            'l10n_br_hr_payroll.hr_salary_structure_FERIAS').id

        self.atribuir_ferias(12, date_from, date_to, employee_id)

        hr_contract_id = self.criar_contrato(
            'Contrato Ferias', 10936.46, hr_payroll_structure_id, employee_id)

        hr_payslip = self.criar_folha_pagamento(
            '2017-01-01', '2017-01-31', hr_contract_id.id, employee_id)

        self.processar_folha_pagamento(hr_payslip)

        self.assertEqual(hr_payslip.line_ids[0].total, 4374.58,
                         'ERRO no Cálculo da rubrica 05 - FERIAS')

    def test_cenario_39(self):
        """
        Rubrica 5 - Férias - Variação 5
        DADO um funcionário com Função Comissionada
        E com Salário Base de R$ 10.936,46
        QUANDO tira 15 dias de Férias no mês
        ENTÃO o cálculo da Rúbrica 5-Férias deve ser R$ 5.486,23
        """
        employee_id = self.employee_hr_user_id.id
        date_from = '2017-02-01 07:00:00'
        date_to = '2017-02-15 17:00:00'

        hr_payroll_structure_id = self.env.ref(
            'l10n_br_hr_payroll.hr_salary_structure_FERIAS').id

        self.atribuir_ferias(15, date_from, date_to, employee_id)

        hr_contract_id = self.criar_contrato(
            'Contrato Ferias', 10936.46, hr_payroll_structure_id, employee_id)

        hr_payslip = self.criar_folha_pagamento(
            '2017-02-01', '2017-02-28', hr_contract_id.id, employee_id)

        self.processar_folha_pagamento(hr_payslip)

        self.assertEqual(hr_payslip.line_ids[0].total, 5468.23,
                         'ERRO no Cálculo da rubrica 05 - FERIAS')

    def test_cenario_44(self):
        """Rubrica 998 - Pagamento de Férias - Variação 2
        DADO um funcionário com Função Comissionada
        E com Salário Base de R$ 10.936,46
        QUANDO tira 10 dias de Férias
        ENTÃO o cálculo da Rubrica 998-Pagamento de Férias deve ser R$ 4.116,74
        """
        pass

    def test_cenario_49(self):
        """Rubrica 1084 - IRRF Férias - Variação 1
        DADO um funcionário com Função Comissionada
        E com Salário Base de R$ 29.483,08
        QUANDO tira 9 dias de Férias no Mês
        E 2 dias de Abono Pecuniário no Mês
        ENTÃO o cálculo da Rubrica 1084-IRRF Férias deve ser R$ 2.216,79
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
