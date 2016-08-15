# -*- coding: utf-8 -*-
# Copyright (C) 2009  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    'name': 'Brazilian Localization Purchase',
    'license': 'AGPL-3',
    'category': 'Localisation',
    'author': 'Akretion, Odoo Community Association (OCA)',
    'website': 'http://odoo-brasil.org',
    'version': '8.0.1.0.0',
    'depends': [
        'l10n_br_stock_account',
        'account_fiscal_position_rule_purchase',
    ],
    'data': [
        'data/l10n_br_purchase_data.xml',
        'views/purchase_view.xml',
        'views/res_company_view.xml',
        'security/ir.model.access.csv',
        'security/l10n_br_purchase_security.xml',
    ],
    'demo': [
        # FIXME
        # 'test/purchase_order_demo.yml'
    ],
    'installable': True,
    'auto_install': False,
}
