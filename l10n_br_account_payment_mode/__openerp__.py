# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Odoo Brazil Account Banking Payment Infrastructure',
    'version': '8.0.1.0.0',
    'category': 'Banking addons',
    'license': 'AGPL-3',
    'summary': '',
    'description': """ """,
    'author': 'KMEE',
    'website': 'http://www.kmee.com.br',
    'depends': [
        'l10n_br_account',
        'l10n_br_data_base',
        'account_due_list_payment_mode',
        'account_banking_payment_export'
    ],
    'data': [
        'views/payment_mode_view.xml',
    ],
    'demo': [
        'demo/payment_demo.xml'
    ],
    'active': True,
}
