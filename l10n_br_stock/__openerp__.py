# -*- coding: utf-8 -*-
# Copyright (C) 2009  Renato Lima - Akretion                                  #
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    'name': 'Brazilian Localization Warehouse',
    'category': 'Localisation',
    'license': 'AGPL-3',
    'author': 'Akretion, Odoo Community Association (OCA)',
    'website': 'http://odoo-brasil.org',
    'version': '8.0.1.0.0',
    'depends': [
        'stock',
    ],
    'data': [
        'data/l10n_br_stock_data.xml',
        'views/stock_view.xml',
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
}
