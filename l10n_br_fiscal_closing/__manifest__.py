# Copyright 2019 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "L10n Br Fiscal Closing",
    "summary": """
        Fechamento fiscal do periodo""",
    "version": "16.0.1.0.1",
    "license": "AGPL-3",
    "author": "KMEE,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-brazil",
    "depends": [
        "l10n_br_fiscal",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/closing.xml",
    ],
    "external_dependencies": {
        "python": [
            "erpbrasil.base>=2.3.0",
        ]
    },
}
