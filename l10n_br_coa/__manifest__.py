# Copyright 2020 KMEE
# Copyright (C) 2020 - TODAY Renato Lima - Akretion
# License AGPL-3.0 or later (http://www.gnu.org/lic enses/agpl).

{
    "name": "Base dos Planos de Contas",
    "summary": """
        Base do Planos de Contas brasileiros""",
    "version": "16.0.2.4.0",
    "license": "AGPL-3",
    "author": "Akretion, KMEE, Odoo Community Association (OCA)",
    "maintainers": ["renatonlima", "mileo"],
    "category": "Accounting",
    "website": "https://github.com/OCA/l10n-brazil",
    "depends": ["account"],
    "data": [
        # security
        "security/ir.model.access.csv",
        # Data
        "data/l10n_br_coa_template.xml",
        "data/account.account.tag.csv",
        "data/account.tax.group.csv",
        "data/account.tax.template.csv",
        # Views
        "views/account_tax_template.xml",
        "views/account_tax.xml",
    ],
    "development_status": "Production/Stable",
    "installable": True,
}
