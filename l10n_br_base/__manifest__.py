# -*- coding: utf-8 -*-
# Copyright (C) 2009 - TODAY Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    'name': 'Brazilian Localization Base',
    'summary': 'Customization of base module for implementations in Brazil.',
    'category': 'Localisation',
    'license': 'AGPL-3',
    'author': (
        'Akretion',
        'Odoo Community Association (OCA)'
    ),
    'website': 'http://odoo-brasil.org',
    'version': '12.0.1.0.0',
    'depends': [
        'base',
        'base_setup',
        'base_address_city',
        'base_address_extended'
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/res.city.csv',
        'data/base_data.xml',
        'data/res.country.state.csv',
        'data/res.bank.csv',
        'views/res_config_settings_view.xml',
        'views/res_city_view.xml',
        'views/res_bank_view.xml',
        'views/res_country_view.xml',
        'views/res_partner_view.xml',
        'views/res_company_view.xml'
    ],
    'demo': [
        'demo/l10n_br_base_demo.xml',
        'demo/res_partner_demo.xml',
    ],
    'installable': True,
    'external_dependencies': {
        'python': ['num2words'],
    }
}
