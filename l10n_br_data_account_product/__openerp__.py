# -*- coding: utf-8 -*-
# Copyright (C) 2009  Renato Lima - Akretion                                  #
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    'name': 'Brazilian Localisation Data Extension for Product',
    'license': 'AGPL-3',
    'author': 'Akretion, Odoo Community Association (OCA)',
    'website': 'http://odoo-brasil.org',
    'version': '8.0.1.0.0',
    'depends': [
        'l10n_br_account_product',
        'l10n_br_data_account',
    ],
    'data': [
        'data/l10n_br_account_product.cest.csv',
        'data/account.product.fiscal.classification.template.csv',
        'data/l10n_br_account_product.icms_relief.csv',
        'data/l10n_br_account_product.ipi_guideline.csv',
    ],
    'demo': [
        'demo/l10n_br_data_account_product_demo.xml',
    ],
    'category': 'Localisation',
    'installable': False,
    'auto_install': True,
}
