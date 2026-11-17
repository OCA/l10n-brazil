# Copyright 2023 - KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "NFS-e (Barueri)",
    "summary": """
        NFS-e (Barueri)""",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "author": "KMEE, Odoo Community Association (OCA)",
    "maintainers": [
        "AndreMarcos",
        "mileo",
        "ygcarvalh",
        "CristianoMafraJunior",
        "marcelsavegnago",
    ],
    "website": "https://github.com/OCA/l10n-brazil",
    "development_status": "Beta",
    "external_dependencies": {
        "python": [
            "erpbrasil.edoc",
            "erpbrasil.assinatura",
            "erpbrasil.transmissao",
            "erpbrasil-base>=2.4.2",
            "nfselib-barueri>=1.1.0",
            "requests",
        ],
    },
    "data": [
        "views/document_view.xml",
        "report/danfse.xml",
        "data/l10n_br_nfse_barueri_cron.xml",
    ],
    "depends": [
        "l10n_br_account",
        "l10n_br_nfse",
    ],
}
