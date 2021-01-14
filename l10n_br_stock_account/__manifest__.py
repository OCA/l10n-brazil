# Copyright (C) 2014  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    'name': 'Brazilian Localization WMS Accounting',
    'category': 'Localisation',
    'license': 'AGPL-3',
    'author': 'Akretion, Odoo Community Association (OCA)',
    'website': 'http://github.com/OCA/l10n-brazil',
    'version': '12.0.1.1.1',
    'depends': [
        'stock_account',
        'stock_picking_invoicing',
        'l10n_br_stock',
        'l10n_br_account',
    ],
    'data': [
        # Security
        'security/ir.model.access.csv',

        # Data
        'data/l10n_br_stock_account_data.xml',

        # Views
        'views/stock_account_view.xml',
        'views/stock_picking.xml',
        'views/stock_rule_view.xml',
        'views/stock_picking_type_view.xml',
        'views/res_company_view.xml',
        'views/fiscal_operation_view.xml',

        # Wizards
        'wizards/stock_invoice_onshipping_view.xml',
        'wizards/stock_return_picking_view.xml',
    ],
    'demo': [
        # Demo
        'demo/company_demo.xml',
        'demo/l10n_br_stock_account_demo.xml',
    ],
    'installable': True,
    'auto_install': True,
}
