# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'CashFlow Report',
    'summary': """
        Financial CashFlow Report""",
    'version': '10.0.1.0.0',
    'license': 'AGPL-3',
    'author': 'KMEE,Odoo Community Association (OCA)',
    'website': 'www.kmee.com.br',
    'depends': [
        'financial',
        'report_xlsx',
        'report_py3o',
    ],
    'data': [
        'wizards/financial_cashflow_wizard_view.xml',
        'reports/financial_cashflow_report.xml',
    ],
}
