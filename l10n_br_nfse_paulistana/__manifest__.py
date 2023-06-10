# Copyright 2019 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "NFS-e (Nota Paulistana)",
    "summary": """
        NFS-e (Nota Paulistana)""",
    "version": "14.0.1.0.0",
    "license": "AGPL-3",
    "author": "KMEE, Odoo Community Association (OCA)",
    "maintainers": ["gabrielcardoso21", "mileo", "luismalta"],
    "development_status": "Beta",
    "website": "https://github.com/OCA/l10n-brazil",
    "external_dependencies": {
        "python": [
            "unidecode",
            "erpbrasil.base>=2.3.0",
            "erpbrasil.edoc",
            "erpbrasil.assinatura>=1.7.0",
            "erpbrasil.transmissao",
            "nfselib.paulistana",
        ],
    },
    "depends": [
        "l10n_br_nfse",
    ],
}
