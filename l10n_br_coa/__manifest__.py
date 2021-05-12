# Copyright 2020 KMEE
# Copyright (C) 2020 - TODAY Renato Lima - Akretion
# License AGPL-3.0 or later (http://www.gnu.org/lic enses/agpl).

{
    'name': 'Brazilian COA',
    'summary': """
        Base Brasilian Localization for the Chart of Accounts""",
    'version': '12.0.3.1.0',
    'license': 'AGPL-3',
    'author': 'Akretion, KMEE, Odoo Community Association (OCA)',
    'website': 'https://github.com/oca/l10n-brazil',
    'depends': ['account'],
    'data': [
        # Data
        'data/l10n_br_coa_template.xml',
        'data/account_tax_tag.xml',
        'data/account_tax_group.xml',
        'data/account_tax_template.xml',
        'data/account_type_data.xml',

        # Views
        'views/account_tax_template.xml',
        'views/account_tax.xml',
    ],
    'development_status': 'Production/Stable',
    'installable': True,
}
