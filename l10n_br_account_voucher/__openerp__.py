# -*- coding: utf-8 -*-
# (C) 2013  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    'name': 'Brazilian Localization Account Voucher',
    'category': 'Localisation',
    'license': 'AGPL-3',
    'author': 'Akretion, KMEE, Odoo Community Association (OCA)',
    'website': 'http://odoo-brasil.org',
    'version': '8.0.1.0.1',
    'depends': [
        'l10n_br_base',
        'l10n_br_account',
        'account_payment',
    ],
    'data': [
        'view/account_journal.xml',
    ],
    'test': [
        'test/account_customer_invoice.yml',
    ],
    'installable': True,
}
