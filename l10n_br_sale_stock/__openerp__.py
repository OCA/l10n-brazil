# -*- coding: utf-8 -*-
# Copyright (C) 2013  Raphaël Valyi - Akretion                                #
# Copyright (C) 2013  Renato Lima - Akretion                                  #
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    'name': 'Brazilian Localization Sales and Warehouse',
    'category': 'Localisation',
    'license': 'AGPL-3',
    'author': 'Akretion, ,Odoo Community Association (OCA)',
    'website': 'http://odoo-brasil.org',
    'version': '8.0.1.0.0',
    'depends': [
        'sale_stock',
        'l10n_br_sale_product',
        'l10n_br_stock_account',
    ],
    'data': [
        'views/sale_stock_view.xml',
        'security/ir.model.access.csv',
    ],
    'demo': [
        'demo/l10n_br_sale_stock_demo.xml'
    ],
    'test': [
        # 'test/sale_order_demo.yml'
    ],
    'installable': True,
    'auto_install': True,
}
