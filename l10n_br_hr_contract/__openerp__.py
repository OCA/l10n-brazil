# -*- coding: utf-8 -*-
# Copyright (C) 2016  Daniel Sadamo - KMEE Informática
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    'name': 'Brazilian Localization HR Contract',
    'category': 'Localisation',
    'license': 'AGPL-3',
    'author': 'KMEE Informática, Odoo Community Association (OCA)',
    'website': 'http://odoo-brasil.org',
    'version': '8.0.0.0.0',
    'depends': [
        'hr_contract',
        'l10n_br_hr',
    ],
    'data': [
        'views/hr_contract_view.xml',
        'data/l10n_br_hr_contract_data.xml',
        'data/l10n_br_hr_contract_resignation_data.xml',
        'security/ir.model.access.csv'
    ],
    'test': [
        'test/l10n_br_hr_contract_demo.yml'
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
}
