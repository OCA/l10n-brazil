# Copyright 2023 - KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "NFS-e (Barueri)",
    "summary": """
        NFS-e (Barueri)""",
    "version": "14.0.1.2.0",
    "license": "AGPL-3",
    "author": "KMEE, Odoo Community Association (OCA)",
    "maintainers": ["AndreMarcos", "mileo", "ygcarvalh"],
    "website": "https://github.com/OCA/l10n-brazil",
    "development_status": "Beta",
    "external_dependencies": {
        "python": [
            "erpbrasil.edoc",
            "erpbrasil.assinatura",
            "erpbrasil.transmissao",
            "erpbrasil.base",
            "nfselib.barueri",
        ],
    },
    "depends": [
        "l10n_br_nfse",
    ],
}
