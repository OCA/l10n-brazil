# -*- coding: utf-8 -*-
# Copyright (C) 2013  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    'name': 'Brazilian Localization Data Account for Service',
    'category': 'Localisation',
    'license': 'AGPL-3',
    'author': 'Akretion, Odoo Community Association (OCA)',
    'website': 'http://odoo-brasil.org',
    'version': '8.0.1.0.0',
    'depends': [
        'l10n_br_account_service',
    ],
    'data': [
        'data/l10n_br_data_account_service_data.xml',
        'data/account_fiscal_position_rule_data.xml',
    ],
    'demo': [
        'demo/l10n_br_data_account_service_demo.xml'
    ],
    'test': [],
    'installable': False,
    'auto_install': True,
}
