# Copyright (C) 2009  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    'name': 'Brazilian Localization Warehouse',
    'category': 'Localisation',
    'license': 'AGPL-3',
    'author': 'Akretion, Odoo Community Association (OCA)',
    'website': 'http://odoo-brasil.org',
    'version': '12.0.1.0.0',
    'depends': [
        'stock',
        'l10n_br_base',
    ],
    'data': [
        'views/stock_view.xml',
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
}
