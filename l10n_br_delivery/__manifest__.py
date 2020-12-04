# Copyright (C) 2020  KMEE INFORMATICA LTDA
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    'name': 'L10n Br Delivery',
    'summary': """
        This module changes the delivery model strategy to match brazilian
        standards.""",
    'license': 'AGPL-3',
    'author': 'KMEE INFORMATICA LTDA,Odoo Community Association (OCA)',
    'website': 'kmee.com.br',
    'version': '12.0.1.1.0',
    'depends': [
        'l10n_br_fiscal',
        'l10n_br_sale_stock',
        'delivery',
    ],
    'data': [
    ],
    'demo': [],
    'category': 'Localisation',
    'installable': True,
}
