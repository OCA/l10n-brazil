# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Odoo Brazil Account Banking Payment Infrastructure',
    'summary': 'Odoo Brazil Payments Mode',
    'version': '8.0.1.0.0',
    'category': 'Banking addons',
    'license': 'AGPL-3',
    'author': "KMEE, Odoo Community Association (OCA)",
    "website": "https://odoo-community.org/",
    'depends': [
        'l10n_br_data_base',
        'l10n_br_account_product',
        'account_due_list_payment_mode',
        'account_banking_payment_export',
        'l10n_br_account_banking_payment',
    ],
    'data': [
        'views/payment_mode_view.xml',
        'views/account_invoice_view.xml',
    ],
    'demo': [
        'demo/payment_demo.xml'
    ],
    'active': True,
}
