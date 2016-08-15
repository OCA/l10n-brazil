# -*- coding: utf-8 -*-
# Copyright (C) 2009  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    'name': 'Brazilian Localisation Data Extension for Account',
    'license': 'AGPL-3',
    'author': 'Akretion, Odoo Community Association (OCA)',
    'website': 'http://odoo-brasil.org',
    'version': '8.0.1.0.1',
    'depends': [
        'l10n_br_account',
    ],
    'data': [
        'data/l10n_br_account.cnae.csv',
        'data/l10n_br_account.service.type.csv',
    ],
    'demo': [
        'demo/base_demo.xml',
    ],
    'category': 'Localisation',
    'installable': True,
    'auto_install': True,
}
