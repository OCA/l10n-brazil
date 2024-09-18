# Copyright 2019 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Fechamento fiscal do período",
    "summary": "Period fiscal closing",
    "version": "14.0.2.0.1",
    "license": "AGPL-3",
    "author": "KMEE,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-brazil",
    "depends": [
        "l10n_br_fiscal_edi",
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
