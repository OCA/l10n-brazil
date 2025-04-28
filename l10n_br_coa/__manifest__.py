# Copyright 2020 KMEE
# Copyright (C) 2020 - TODAY Renato Lima - Akretion
# License AGPL-3.0 or later (http://www.gnu.org/lic enses/agpl).

{
    "name": "Base dos Planos de Contas",
    "summary": """
        Base do Planos de Contas brasileiros""",
    "version": "17.0.1.0.0",
    "license": "AGPL-3",
    "author": "Akretion, KMEE, Odoo Community Association (OCA)",
    "maintainers": ["renatonlima", "mileo"],
    "category": "Accounting/Localizations/Account Charts",
    "website": "https://github.com/OCA/l10n-brazil",
    "depends": ["account"],
    "data": [
        # Data
        "data/account_tax_tag.xml",
        # Views
        "views/account_tax.xml",
    ],
    "development_status": "Production/Stable",
    "installable": True,
}
