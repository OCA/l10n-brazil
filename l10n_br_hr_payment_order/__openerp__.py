# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'L10n Br Hr Payment Order',
    'summary': """
        Integração da folha de pagamento com as ordens de pagamento""",
    'version': '8.0.1.0.0',
    'license': 'AGPL-3',
    'author': 'KMEE,Odoo Community Association (OCA)',
    'website': 'www.kmee.com.br',
    'depends': [
        'l10n_br_hr_payroll',
        'account_payment',
        'account_payment_partner',
        'l10n_br_account_banking_payment_cnab',
    ],
    'data': [
        'data/hr_salary_rule.xml',
        'security/hr_payslip.xml',
        'security/payment_order.xml',
        'security/ir.model.access.csv',
        'wizard/payslip_payment_create_order_view.xml',
        'views/hr_payslip.xml',
        'views/payment_order.xml',
        'views/res_config_view.xml',
        'views/hr_salary_rule_view.xml',
        'hr_payroll_workflow.xml',
        'payment_order_workflow.xml',
        'views/hr_contract.xml',
    ],
    'demo': [
        'demo/hr_payslip.xml',
        'demo/payment_order.xml',
    ],
}
