# Copyright 2024 Escodoo
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "L10n Br Account Withholding",
    "summary": """
        Brazilian Withholding Invoice Generator""",
    "version": "14.0.1.2.1",
    "license": "AGPL-3",
    "author": "Escodoo,Akretion,Odoo Community Association (OCA)",
    "maintainers": ["marcelsavegnago", "renatonlima"],
    "website": "https://github.com/OCA/l10n-brazil",
    "depends": [
        "l10n_br_account",
    ],
    "data": [
        "views/l10n_br_fiscal_tax_group.xml",
        "views/account_move.xml",
    ],
    "demo": [
        "demo/ir.property.xml",
    ],
}
