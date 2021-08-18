# Copyright 2020 KMEE
# Copyright (C) 2020 - TODAY Renato Lima - Akretion
# License AGPL-3.0 or later (http://www.gnu.org/lic enses/agpl).

{
    "name": "Base do plano de conta",
    "summary": """
        Base do plano de conta brasileiro""",
    "version": "13.0.1.0.0",
    "license": "AGPL-3",
    "author": "Akretion, KMEE, Odoo Community Association (OCA)",
    "maitainers": ["renatonlima", "mileo"],
    "category": "Accounting",
    "website": "https://github.com/OCA/l10n-brazil",
    "depends": ["account"],
    "data": [
        # Data
        "data/l10n_br_coa_template.xml",
        "data/account_tax_tag.xml",
        "data/account_tax_group.xml",
        "data/account_tax_template.xml",
        "data/account_type_data.xml",
        # Views
        "views/account_tax_template.xml",
        "views/account_tax.xml",
    ],
    "development_status": "Production/Stable",
    "installable": True,
}
