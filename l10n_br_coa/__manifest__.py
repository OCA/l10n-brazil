# Copyright 2020 KMEE
# Copyright (C) 2020 - TODAY Renato Lima - Akretion
# License AGPL-3.0 or later (http://www.gnu.org/lic enses/agpl).

{
    'name': 'L10n Br Coa',
    'summary': """
        Base Brasilian Localization of Chart of Account""",
    'version': '14.0.1.0.0',
    'license': 'AGPL-3',
    'author': 'Akretion, KMEE, Odoo Community Association (OCA)',
    'website': 'https://github.com/oca/l10n-brazil',
    "maintainers": ["renatonlima", "gabrielcardoso21", "mileo"],
    'depends': ['account'],
    'data': [
        # Data
        'data/l10n_br_coa_template.xml',
        'data/account_tax_tag.xml',
        'data/account_tax_group.xml',
        'data/account_tax_template.xml',
    ],
    'installable': True,
}
