# -*- coding: utf-8 -*-
# Copyright (C) 2016-Today - KMEE (<http://kmee.com.br>).
#  Luis Felipe Miléo - mileo@kmee.com.br
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Brazilian Banking - Debit and Payments Export Infrastructure',
    'version': '8.0.1.0.0',
    'license': 'AGPL-3',
    'author': "KMEE, "
              "Odoo Community Association (OCA)",
    'website': 'https://github.com/odoo-brazil/odoo-brazil-banking',
    'category': 'Banking addons',
    'depends': [
        'l10n_br_account',
        'account_banking_payment_export',
        'account_due_list',
    ],
    'data': [
        'views/account_due_list.xml',
        'views/account_payment.xml',
        'wizard/payment_order_create_view.xml',
    ],
    'demo': [
    ],
    'installable': True,
}
