# -*- coding: utf-8 -*-
# Copyright (C) 2013  Renato Lima - Akretion                                  #
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    'name': 'Brazilian Localization Account Voucher',
    'category': 'Localisation',
    'license': 'AGPL-3',
    'author': 'Akretion, OpenERP Brasil',
    'website': 'http://openerpbrasil.org',
    'version': '7.0',
    'depends': [
        'l10n_br_base',
        'l10n_br_account',
        'account_payment',
    ],
    'data': [
        'wizard/account_statement_from_invoice_view.xml',
    ],
    'demo': [
    ],
    'installable': False,
}
