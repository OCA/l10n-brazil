# -*- coding: utf-8 -*-
# Copyright (C) 2016 KMEE (http://www.kmee.com.br)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    'name': 'Brazilian Localization HR Payroll',
    'category': 'Localization',
    'license': 'AGPL-3',
    'author': 'KMEE, Odoo Community Association (OCA)',
    'maintainer': 'KMEE',
    'website': 'http://www.kmee.com.br',
    'version': '8.0.0.0.1',
    'depends': [
        'l10n_br_hr_holiday',
        'l10n_br_resource',
        'l10n_br_hr_contract',
        'hr_payroll',
    ],
    'data': [
        'data/l10n_br_hr_income_tax.xml',
        'data/l10n_br_hr_income_tax_deductable_amount_family.xml',
        'views/hr_contract.xml',
        'security/l10n_br_hr_contract.xml',
        'views/l10n_br_hr_contract.xml',
        'views/l10n_br_hr_contract_cargo_atividade.xml',
        'views/l10n_br_hr_contract_filiacao_sindical.xml',
        'views/l10n_br_hr_contract_jornada.xml',
        'views/l10n_br_hr_contract_lotacao_local.xml',
        'views/l10n_br_hr_contract_remuneracao.xml',
        'data/l10n_br_hr_payroll_data_rubricas.xml',
        'data/l10n_br_hr_payroll_data_tabela_INSS.xml',
        'security/ir.model.access.csv',
        'views/l10n_br_hr_child_benefit_view.xml',
        'views/l10n_br_hr_income_tax_view.xml',
        'views/l10n_br_hr_income_tax_deductable_amount_family_view.xml',
        'views/l10n_br_hr_minimum_wage_view.xml',
        'views/l10n_br_hr_rat_fap_view.xml',
        'views/l10n_br_hr_social_security_tax_view.xml',
        'views/hr_payslip.xml',
        'views/hr_salary_rule.xml',
    ],
    'installable': True,
    'auto_install': False,
}
