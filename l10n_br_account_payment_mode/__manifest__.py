# -*- coding: utf-8 -*-
# Copyright (C) 2017-Today - KMEE (<http://kmee.com.br>).
#  @author Luis Felipe Miléo - mileo@kmee.com.br
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Odoo Brazil Account Banking Payment Infrastructure',
    'summary': 'Odoo Brazil Payments Mode',
    'version': '10.0.1.0.0',
    'category': 'Banking addons',
    'license': 'AGPL-3',
    'author': "KMEE, Odoo Community Association (OCA)",
    "website": "https://odoo-community.org/",
    'depends': [
        'l10n_br_account_banking_payment',
        'l10n_br_account_product',
        'account_due_list_payment_mode',
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
