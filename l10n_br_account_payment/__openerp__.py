# -*- coding: utf-8 -*-
# Copyright (C) 2011  Renato Lima - Akretion                                  #
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    'name': 'Brazilian Localization Account Payment',
    'description': 'Brazilian Localization Account Payment',
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
        'l10n_br_account_payment_data.xml',
        'account_invoice_view.xml',
        'security/ir.model.access.csv',
        'security/l10n_br_account_payment_security.xml',
    ],
    'demo': [
        'l10n_br_account_payment_demo.xml',
    ],
    'installable': False,
}
