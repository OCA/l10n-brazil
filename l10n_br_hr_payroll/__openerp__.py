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
        'hr_payroll',
        'l10n_br_hr_resource',
        'l10n_br_hr_holiday',
        'l10n_br_hr_contract',
        'l10n_br_hr_vacation',
    ],
    'external_dependencies': {
        'python': ['pybrasil'],
    },
    'data': [
        'data/hr_contract_category.xml',
        'data/hr_payroll_type.xml',
        'data/l10n_br_hr_payroll_categorias.xml',
        'data/l10n_br_hr_contract_sequence.xml',
        'data/l10n_br_hr_tabela_INSS.xml',
        'data/l10n_br_hr_tabela_IR.xml',
        'data/l10n_br_hr_tabela_IR_dependente.xml',
        'data/l10n_br_hr_tabela_RAT_FAP.xml',
        'data/l10n_br_hr_payroll_decimal_precision.xml',

        'security/l10n_br_hr_contract.xml',
        'security/l10n_br_hr_payslip_security_rule.xml',
        'security/l10n_br_hr_rat_fap_security_rule.xml',
        'security/hr_telefonia_line_security_rule.xml',
        'security/ir.model.access.csv',

        'views/hr_contract.xml',
        'views/hr_contract_category.xml',
        'views/hr_department_view.xml',
        'views/hr_contract_autonomo.xml',
        'views/hr_contract_menu.xml',
        'views/l10n_br_hr_employee.xml',
        'views/hr_payroll_structure.xml',
        'views/hr_payslip.xml',
        'views/hr_payslip_autonomo.xml',
        'views/hr_payslip_run.xml',
        'views/hr_salary_rule.xml',
        'views/l10n_br_hr_child_benefit_view.xml',
        'views/l10n_br_hr_income_tax_deductable_amount_family_view.xml',
        'views/l10n_br_hr_income_tax_view.xml',
        'views/l10n_br_hr_minimum_wage_view.xml',
        'views/l10n_br_hr_rat_fap_view.xml',
        'views/l10n_br_hr_social_security_tax_view.xml',
        'views/res_config_view.xml',
        'views/hr_telefonia_view.xml',
        
        # Alterações Contratuais
        'views/l10n_br_hr_contract_change/l10n_br_hr_contract_change_menu.xml',
        'views/l10n_br_hr_contract_change/l10n_br_hr_contract_change_base.xml',
        'views/l10n_br_hr_contract_change/remuneracao.xml',
        'views/l10n_br_hr_contract_change/lotacao_local.xml',
        'views/l10n_br_hr_contract_change/jornada.xml',
        'views/l10n_br_hr_contract_change/filiacao_sindical.xml',
        'views/l10n_br_hr_contract_change/cargo_atividade.xml',

        'views/l10n_br_hr_acordo_coletivo.xml',

        # wizards
        'wizards/hr_ateste_telefonia_wizard.xml',

    ],
    'demo': [
        # 'demo/hr_contract.xml',
        # 'demo/l10n_br_hr_payroll_rubricas.xml',
        # 'demo/l10n_br_hr_payroll_estruturas.xml',
    ],
    'installable': True,
    'auto_install': False,
}
