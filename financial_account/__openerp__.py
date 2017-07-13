# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Financial Account',
    'summary': """
        Integrate financial module with Odoo accounting""",
    'version': '8.0.1.0.0',
    'license': 'AGPL-3',
    'author': 'KMEE,Odoo Community Association (OCA)',
    'website': 'www.kmee.com.br',
    'depends': [
        'financial',
        'account',
    ],
    'data': [
        'security/financial_account_move_matrix.xml',
        'views/inherited_res_partner_bank_view.xml',
        'views/inherited_financial_move_debt_base_view.xml',
        'views/inherited_financial_move_payment_base_view.xml',
        'views/financial_account_move_template_view.xml',
        'views/inherited_financial_account_view.xml',

        'security/ir.model.access.csv',
    ],
    'demo': [
    ],
    'installable': True,
}
