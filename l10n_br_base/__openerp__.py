# -*- coding: utf-8 -*-
# Copyright (C) 2009 - TODAY Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    'name': 'Brazilian Localization Base',
    'category': 'Localisation',
    'license': 'AGPL-3',
    'author': 'Akretion, Odoo Community Association (OCA)',
    'website': 'http://odoo-brasil.org',
    'version': '9.0.1.0.0',
    'depends': [
        'base',
        'base_setup',
    ],
    'data': [
        'data/res.country.state.csv',
        'data/l10n_br_base.city.csv',
        'data/l10n_br_base_data.xml',
        'views/l10n_br_base_view.xml',
        'views/res_bank_view.xml',
        'views/res_country_view.xml',
        'views/res_partner_view.xml',
        'views/res_company_view.xml',
        'security/ir.model.access.csv',
    ],
    'demo': [
        'demo/l10n_br_base_demo.xml',
        'demo/res_partner_demo.xml',
    ],
    'test': [
        'test/base_inscr_est_valid.yml',
        'test/base_inscr_est_invalid.yml',
        'test/res_partner_test.yml',
        'test/res_company_test.yml',
    ],
    'installable': True,
    'auto_install': False,
    'external_dependencies': {
        'python': ['num2words'],
    }
}
