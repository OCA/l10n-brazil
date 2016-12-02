# -*- coding: utf-8 -*-
# Copyright (C) 2010  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    'name': 'Brazilian Localization Delivery',
    'license': 'AGPL-3',
    'author': 'Akretion, Odoo Community Association (OCA)',
    'website': 'http://odoo-brasil.org',
    'version': '8.0.1.0.0',
    'depends': [
        'l10n_br_sale_stock',
        'delivery',
    ],
    'data': [
        'views/account_invoice_view.xml',
        'views/delivery_view.xml',
        'views/stock_view.xml',
        'views/l10n_br_delivery_view.xml',
        'security/ir.model.access.csv',
    ],
    'demo': [],
    'category': 'Localisation',
    'installable': False,
}
