# Copyright (C) 2013  Raphaël Valyi - Akretion
# Copyright (C) 2013  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    'name': 'Brazilian Localization Sales and Warehouse',
    'category': 'Localization',
    'license': 'AGPL-3',
    'author': 'Akretion, Odoo Community Association (OCA)',
    'website': 'http://github.com/OCA/l10n-brazil',
    'version': '12.0.1.0.0',
    'depends': [
        'sale_stock',
        'l10n_br_sale',
        'l10n_br_stock_account',
    ],
    'data': [],
    'demo': [
        'demo/l10n_br_sale_stock_demo.xml',
    ],
    'installable': True,
    'auto_install': True,
}
