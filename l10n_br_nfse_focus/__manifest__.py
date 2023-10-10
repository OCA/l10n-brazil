# Copyright 2023 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "NFS-e (FocusNFE)",
    "summary": """
        NFS-e (FocusNFE)""",
    "version": "14.0.1.0.0",
    "license": "AGPL-3",
    "author": "KMEE, Odoo Community Association (OCA)",
    "maintainers": ["AndreMarcos", "mileo", "ygcarvalh"],
    "website": "https://github.com/OCA/l10n-brazil",
    "development_status": "Beta",
     "external_dependencies": {
        "python": [
            "erpbrasil.assinatura",
            "erpbrasil.base>=2.3.0",
            "nfelib>=2.0.0",
            "xsdata",
        ],
    },
    "depends": [
        "l10n_br_nfse",
    ],
    "data" : [
        "views/res_company.xml",
    ]
}
