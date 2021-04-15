# Copyright (C) 2020  KMEE INFORMATICA LTDA
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    'name': 'Brazilian Localization Delivery',
    'summary': """
        This module changes the delivery model strategy to match brazilian
        standards.""",
    'license': 'AGPL-3',
    'author': 'KMEE,Odoo Community Association (OCA)',
    'website': 'https://github.com/oca/l10n-brazil',
    'version': '12.0.3.0.0',
    'depends': [
        'l10n_br_fiscal',
        'l10n_br_sale_stock',
        'delivery',
    ],
    'data': [
    ],
    'demo': [],
    'category': 'Localization',
    'installable': True,
}
