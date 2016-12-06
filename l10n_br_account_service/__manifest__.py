# -*- coding: utf-8 -*-
# Copyright (C) 2009-2013  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    'name': 'Brazilian Localization Account Service',
    'category': 'Localisation',
    'license': 'AGPL-3',
    'author': 'Akretion, Odoo Community Association (OCA)',
    'website': 'http://odoo-brasil.org',
    'version': '8.0.2.0.0',
    'depends': [
        'l10n_br_account',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/l10n_br_account_service_data.xml',
        'views/product_view.xml',
        'views/l10n_br_account_view.xml',
        'views/res_company_view.xml',
        'views/account_invoice_view.xml',
        'views/nfse/account_invoice_nfse_view.xml',
    ],
    'demo': [
        'demo/account_tax_demo.xml',
        'demo/product_demo.xml',
        'demo/l10n_br_account_service_demo.xml',
        'demo/account_fiscal_position_rule_demo.xml',
    ],
    'test': [
        'test/account_customer_invoice.yml',
        # 'test/account_invoice_refund.yml',
    ],
    'installable': False,
    'auto_install': False,
}
