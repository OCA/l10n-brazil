# -*- coding: utf-8 -*-
# Copyright (C) 2009 - TODAY Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    'name': 'Brazilian Localization Base',
    'category': 'Localisation',
    'license': 'AGPL-3',
    'author': 'Akretion, Odoo Community Association (OCA)',
    'website': 'http://odoo-brasil.org',
    'version': '10.0.1.0.0',
    'depends': [
        'base',
        'base_setup',
    ],
    'data': [
        'security/inherited_res_groups_data.xml',
        'security/ir.model.access.csv',
        'data/inherited_res_country_state_data.xml',
        'data/ir_config_paramater.xml',
        'data/l10n_br_base.city.csv',
        'data/l10n_br_base_data.xml',
        'data/res.country.state.csv',
        'views/l10n_br_base_menu.xml',
        'views/l10n_br_base_config.xml',
        'views/l10n_br_base_city_view.xml',
        'views/res_bank_view.xml',
        'views/res_country_view.xml',
        'views/res_partner_view.xml',
        'views/res_company_view.xml',
        'data/l10n_br_city_exterior_data.xml',
    ],
    'demo': [
        'demo/l10n_br_base_demo.xml',
        'demo/res_partner_demo.xml',
    ],
    'installable': True,
    'auto_install': False,
    'external_dependencies': {
        'python': ['num2words'],
    }
}
