# -*- coding: utf-8 -*-
# Copyright 2019 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'L10n Br Hr Benefit',
    'summary': """
        Benefícios de Funcionários (Alimentação / Baba / Cesta /
 Creche / Refeição / Saúde / Vida)""",
    'version': '8.0.1.0.0',
    'license': 'AGPL-3',
    'author': 'KMEE INFORMATICA LTDA,Odoo Community Association (OCA)',
    'website': 'www.kmee.com.br',
    'depends': [
        'l10n_br_hr_payroll',
    ],
    'data': [
        'views/hr_benefit_menu.xml',

        'wizards/wizard_hr_contract_benefit_create.xml',
        'wizards/wizard_hr_contract_benefit_periodic.xml',

        'views/hr_benefit_type.xml',
        'views/hr_contract_benefit_line.xml',
        'views/hr_contract_benefit.xml',
        'wizards/wizard_benefit_exception_cause.xml',
        'views/hr_contract.xml',
        'views/hr_employee.xml',
        'views/hr_employee_dependent.xml',
        'data/hr_contract_benefit_periodic_cron.xml',

        'security/ir.model.access.csv',
        'security/ir_rules.xml',




        # 'security/hr_employee_dependent.xml',
        # 'security/hr_employee.xml',
        # 'security/hr_benefit_type.xml',
        # 'security/hr_contract_benefit_line.xml',
        # 'security/hr_contract_benefit.xml',
    ],
    'demo': [
        # 'demo/hr_employee_dependent.xml',
        # 'demo/hr_employee.xml',
        # 'demo/hr_benefit_type.xml',
        # 'demo/hr_contract_benefit_line.xml',
        # 'demo/hr_contract_benefit.xml',
    ],
}
