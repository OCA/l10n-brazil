# Copyright 2023 Akretion
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "NFS-e (padrão nacional)",
    "summary": """
        NFS-e (padrão nacional)""",
    "version": "14.0.1.0.0",
    "license": "AGPL-3",
    "author": "Akretion, Odoo Community Association (OCA)",
    "maintainers": ["rvalyi"],
    "development_status": "Alpha",
    "website": "https://github.com/OCA/l10n-brazil",
    "external_dependencies": {
        "python": [
            "erpbrasil.assinatura>=1.7.0",
            "erpbrasil.base>=2.3.0",
            "nfelib>=2.0.0",
            "xsdata",
        ],
    },
    "depends": [
        "l10n_br_nfse",
    ],
}
