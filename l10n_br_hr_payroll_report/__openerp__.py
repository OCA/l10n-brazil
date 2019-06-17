# -*- coding: utf-8 -*-
# Copyright 2017 KMEE - Hendrix Costa <hendrix.costa@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Reports for l10n_br_hr_payslip',
    'summary': 'Reports for l10n_br_hr_payslip',
    'version': '8.0.1.0.0',
    'category': 'Reports',
    'website': 'http://www.kmee.com.br',
    'author': "KMEE, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    'depends': [
        'l10n_br_hr_payroll',
        'report_py3o',
    ],
    'data': [
        'reports/payslip_report_analitico.xml',
        'reports/payslip_report_aviso_ferias.xml',
        'reports/payslip_report_recibo_ferias.xml',
        'reports/payslip_report_holerite.xml',
        'reports/payslip_report_holerite_autonomo_rpa.xml',
        'reports/payslip_report_rescisao.xml',
        'reports/payslip_report_ficha_registro.xml',
        'reports/payslip_run_report_telefonia.xml',
        'wizards/wizard_l10n_br_hr_payroll_analytic_report.xml',
        'wizards/wizard_l10n_br_hr_employee_ficha_registro.xml',
        'views/hr_salary_rule.xml',
        'views/hr_field_rescission.xml',
        'views/hr_employee.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
}
