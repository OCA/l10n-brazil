# -*- coding: utf-8 -*-
# Copyright (C) 2016 KMEE (http://www.kmee.com.br)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp.tests import common


class TestL10nBrHrSyndicates(common.TransactionCase):

    def setUp(self):
        super(TestL10nBrHrSyndicates, self).setUp()
        self.job_obj = self.env['hr.job']
        self.res_users_obj = self.env['res.users']
        self.employee_obj = self.env['hr.employee']
        self.collectives_conventions_obj = self.env[
            'l10n.br.hr.collectives.conventions'
        ]
        self.job_minimum_wage_obj = self.env['l10n.br.hr.job.minimum.wage']
        self.job_rubric_obj = self.env['l10n.br.hr.job.rubric']
        self.job_fix_rubric_obj = self.env['l10n.br.hr.job.fix.rubric']
        self.syndicate_contribution_obj = self.env[
            'l10n.br.hr.syndicate.contribution'
        ]
        self.job_id = self.job_obj.create(
            {
                'name': 'Analista de Sistemas',
            }
        )
        self.user_id = self.res_users_obj.create({
            'name': 'João Pedro',
            'login': 'joaopedro',
            'alias_name': 'User Joao',
            'email': 'joaopedro@email.com',
        })
        self.employee_id = self.employee_obj.create({
            'name': 'João Pedro',
            'user_id': self.user_id.id,
        })

    def criar_convencoes_coletivas(self):
        vals = {
            'agreement_date': '2017-01-01',
            'agreement_type': 'Verbal',
            'process_number': 12345,
            'vara': u'Segunda Vara do Cartório de Itajubá',
            'base_year': '2017-01-01',
        }
        return self.collectives_conventions_obj.create(vals)

    def criar_salario_minimo_cargo(self):
        vals = {
            'preferential_workload': 8,
            'hour_minimum_wage': 100.00,
            'date_beginning': '2017-01-01',
            'job_id': self.job_id.id,
            'month_minimum_wage': 850.00,
        }
        return self.job_minimum_wage_obj.create(vals)

    def criar_rubricas_por_cargo(self):
        vals = {
            'job_id': self.job_id.id,
            'data_beginning': '2017-01-01',
            'data_ending': '2017-12-30',
            'rubric_id': self.env.ref(
                'l10n_br_hr_payroll.hr_salary_rule_REMBOLSO_PLANO_SAUDE').id,
            'reference': 'ABC-013',
            'value': 400.00,
            'percentage': 100,
            'quantity': 1,
        }
        return self.job_rubric_obj.create(vals)

    def criar_rubricas_fixas_por_cargo(self):
        vals = {
            'date_ending': '2017-12-30',
            'final_wage': 850.00,
            'value': 200.00,
            'initial_wage': 450.00,
            'rubric_id': self.env.ref(
                'l10n_br_hr_payroll.hr_salary_rule_REMBOLSO_PLANO_SAUDE').id,
            'reference': 'ABC-123',
            'date_beginning': '2017-01-01',
            'monthly_hourly': self.employee_id.id,
            'percentage': 100,
            'quantity': 1,
        }
        return self.job_fix_rubric_obj.create(vals)

    def criar_contribuicao_sindical(self):
        vals = {
            'aliquot': 7.50,
            'additional_portion': 1.50,
            'social_capital_class': 'Empregado',
        }
        return self.syndicate_contribution_obj.create(vals)

    def test_criar_convencoes_coletivas(self):
        convencao_coletiva = self.criar_convencoes_coletivas()
        self.assertEqual(
            convencao_coletiva.agreement_date,
            '2017-01-01',
            "Data do acordo está incorreta!"
        )
        self.assertEqual(
            convencao_coletiva.agreement_type,
            'Verbal',
            "Tipo do acordo está incorreta!"
        )
        self.assertEqual(
            convencao_coletiva.process_number,
            12345,
            "Número do processo está incorreto!"
        )
        self.assertEqual(
            convencao_coletiva.vara,
            u'Segunda Vara do Cartório de Itajubá',
            "Vara está incorreto!"
        )
        self.assertEqual(
            convencao_coletiva.base_year,
            '2017-01-01',
            "Ano base está incorreto!"
        )

    def test_criar_salario_minimo_cargo(self):
        salario_minimo_cargo = self.criar_salario_minimo_cargo()
        self.assertEqual(
            salario_minimo_cargo.preferential_workload,
            8,
            "A carga de trabalho de preferência está incorreta",
        )
        self.assertEqual(
            salario_minimo_cargo.hour_minimum_wage,
            100.00,
            "O Salário minimo por hora está incorreto!"
        )
        self.assertEqual(
            salario_minimo_cargo.date_beginning,
            '2017-01-01',
            "A data de inicio está incorreta!"
        )
        self.assertEqual(
            salario_minimo_cargo.job_id,
            self.job_id,
            "O cargo está incorreto!"
        )
        self.assertEqual(
            salario_minimo_cargo.month_minimum_wage,
            850.00,
            "O salário mínimo está incorreto!"
        )

    def test_rubricas_por_cargo(self):
        rubricas_por_cargo = self.criar_rubricas_por_cargo()
        self.assertEqual(
            rubricas_por_cargo.job_id,
            self.job_id,
            "O cargo está incorreto!"
        )
        self.assertEqual(
            rubricas_por_cargo.data_beginning,
            '2017-01-01',
            "A data de inicio está incorreta!"
        )
        self.assertEqual(
            rubricas_por_cargo.data_ending,
            '2017-12-30',
            "A data de fim está incorreta!"
        )
        self.assertEqual(
            rubricas_por_cargo.rubric_id,
            self.env.ref(
                'l10n_br_hr_payroll.hr_salary_rule_REMBOLSO_PLANO_SAUDE'),
            "A rubrica está incorreta!"
        )
        self.assertEqual(
            rubricas_por_cargo.reference,
            'ABC-013',
            "A referência está incorreta!"
        )
        self.assertEqual(
            rubricas_por_cargo.percentage,
            100,
            "A porcentagem está incorreta!"
        )
        self.assertEqual(
            rubricas_por_cargo.quantity,
            1,
            "A quantidade está incorreta!"
        )

    def test_rubricas_fixas_por_cargo(self):
        rubricas_fixas_por_cargo = self.criar_rubricas_fixas_por_cargo()
        self.assertEqual(
            rubricas_fixas_por_cargo.date_ending,
            '2017-12-30',
            "A data final está incorreta"
        )
        self.assertEqual(
            rubricas_fixas_por_cargo.final_wage,
            850.00,
            "O salário final está incorreto!"
        )
        self.assertEqual(
            rubricas_fixas_por_cargo.value,
            200.00,
            "O valor está incorreto!"
        )
        self.assertEqual(
            rubricas_fixas_por_cargo.initial_wage,
            450.00,
            "O salário inicial está incorreto!"
        )
        self.assertEqual(
            rubricas_fixas_por_cargo.rubric_id,
            self.env.ref(
                'l10n_br_hr_payroll.hr_salary_rule_REMBOLSO_PLANO_SAUDE'),
            "A rubrica está incorreta!"
        )
        self.assertEqual(
            rubricas_fixas_por_cargo.reference,
            "ABC-123",
            "A referencia está incorreta!"
        )
        self.assertEqual(
            rubricas_fixas_por_cargo.date_beginning,
            '2017-01-01',
            "A data de inicio está incorreta!",
        )
        self.assertEqual(
            rubricas_fixas_por_cargo.monthly_hourly,
            self.employee_id,
            "O empregado está incorreto!"
        )
        self.assertEqual(
            rubricas_fixas_por_cargo.percentage,
            100,
            "A porcentagem está incorreta!"
        )
        self.assertEqual(
            rubricas_fixas_por_cargo.quantity,
            1,
            "A quantidade está incorreta!"
        )

    def test_contribuicao_sindical(self):
        contribuicao_sindical = self.criar_contribuicao_sindical()
        self.assertEqual(
            contribuicao_sindical.aliquot,
            7.50,
            "A aliquota está incorreta!"
        )
        self.assertEqual(
            contribuicao_sindical.additional_portion,
            1.50,
            "A porção adicional está incorreta!"
        )
        self.assertEqual(
            contribuicao_sindical.social_capital_class,
            "Empregado",
            "A classe social está incorreta!"
        )
