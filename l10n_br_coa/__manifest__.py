# Copyright 2020 KMEE
# Copyright (C) 2020 - TODAY Renato Lima - Akretion
# License AGPL-3.0 or later (http://www.gnu.org/lic enses/agpl).

{
    "name": "Base dos Planos de Contas",
    "summary": """
        Base do Planos de Contas brasileiros""",
    "version": "19.0.1.0.1",
    "license": "AGPL-3",
    "author": "Akretion, KMEE, Odoo Community Association (OCA)",
    "maintainers": ["renatonlima", "mileo"],
    "category": "Accounting/Localizations/Account Charts",
    "website": "https://github.com/OCA/l10n-brazil",
    "depends": ["account"],
    "data": [
        # security
        # Data
        # "data/l10n_br_coa_template.xml",
        "data/account.account.tag.csv",
        # "data/template/account.tax.group.csv",
        # "data/template/account.tax.csv",
        #        "data/account.tax.template.csv",
        # Views
        "views/account_tax.xml",
    ],
    "oca_data_manual": [
        "data/l10n_br_coa_tax_accounts.csv",
        "data/l10n_br_coa_tax_templates_accounts.csv",
        "data/l10n_br_coa_template.xml",
        "views/account_tax_template.xml",
    ],
    "development_status": "Production/Stable",
    "installable": True,
}
