# Copyright (C) 2009 - TODAY Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    'name': 'Brazilian Localization Account',
    'category': 'Localisation',
    'license': 'AGPL-3',
    'author': 'Akretion, Odoo Community Association (OCA)',
    'website': 'http://odoobrasil.org',
    'version': '12.0.1.0.0',
    'depends': [
        'l10n_br',
        'l10n_br_base',
        'account_cancel',
        'fiscal',
        'account_fiscal_position_rule',
    ],
    'data': [
        #'security/ir.model.access.csv',
        #'data/l10n_br_account_data.xml',
        #'views/account_view.xml',
        #'views/account_invoice_view.xml',
        #'views/product_view.xml',
        #'views/res_company_view.xml',
        #'report/account_invoice_report_view.xml',
    ],
    'demo': [
        'demo/base_demo.xml'
    ],
    'installable': True,
    'auto_install': False,
}
