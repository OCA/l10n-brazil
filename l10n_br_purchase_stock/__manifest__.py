# Copyright (C) 2009  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    'name': 'Brazilian Localization Purchase Stock',
    'license': 'AGPL-3',
    'category': 'Localisation',
    'author': 'Akretion, Odoo Community Association (OCA)',
    'website': 'http://odoo-brasil.org',
    'version': '12.0.1.1.0',
    'depends': [
        'l10n_br_purchase',
        'l10n_br_stock_account',
    ],
    'data': [
        # Views
        'views/purchase_order.xml',
        'views/res_config_settings.xml',
    ],
    'installable': True,
    'auto_install': True,
}
