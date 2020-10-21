# Copyright 2020 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'L10n Br Coa',
    'summary': """
        Base Brasilian Localization of Chart of Account""",
    'version': '12.0.1.1.0',
    'license': 'AGPL-3',
    'author': 'Akretion, KMEE, Odoo Community Association (OCA)',
    'website': 'https://github.com/oca/l10n-brazil',
    'depends': ['account'],
    'data': [
        # Security
        'security/l10n_br_account_tax_template.xml',

        # Data
        'data/account_tax_tag.xml',
        'data/account_tax_group_data.xml',
        'data/l10n_br_account_tax_template_data.xml',

        # Views
        'views/l10n_br_account_tax_template.xml',
        'views/account_tax_template.xml',
        'views/account_tax.xml',
    ],
    'installable': True,
}
