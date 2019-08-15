# -*- coding: utf-8 -*-
# Copyright (C) 2009  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    'name': 'Brazilian Localization Sale',
    'category': 'Localisation',
    'license': 'AGPL-3',
    'author': 'Akretion, Odoo Community Association (OCA)',
    'website': 'http://odoo-brasil.org',
    'version': '10.0.1.0.0',
    'depends': [
        'account_fiscal_position_rule_sale',
        'l10n_br_account',
    ],
    'data': [
        'data/l10n_br_sale_data.xml',
        'views/sale_view.xml',
        'views/res_config_view.xml',
        'security/ir.model.access.csv',
        'security/l10n_br_sale_security.xml',
        'report/sale_report_view.xml',
        'views/res_company_view.xml',
    ],
    'demo': [
        'demo/l10n_br_sale_demo.xml',
    ],
    'installable': True,
    'auto_install': True,
    'development_status': 'Production/Stable',
    'maintainers': ['renatonlima']
}
