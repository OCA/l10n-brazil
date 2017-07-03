# -*- coding: utf-8 -*-
# Copyright (C) 2014  Renato Lima - Akretion                                  #
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    'name': 'Brazilian Localization Sale Product',
    'category': 'Localisation',
    'license': 'AGPL-3',
    'author': 'Akretion, Odoo Community Association (OCA)',
    'website': 'http://odoo-brasil.org',
    'version': '8.0.1.0.0',
    'depends': [
        'l10n_br_sale',
        'l10n_br_account_product',
    ],
    'data': [
        'views/sale_view.xml',
        'views/res_company_view.xml',
        'data/l10n_br_sale_product_data.xml',
        'security/ir.model.access.csv',
    ],
    'test': [],
    'demo': [
        'demo/product_demo.xml',
    ],
    'installable': True,
    'auto_install': True,
}
