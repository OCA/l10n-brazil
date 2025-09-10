# Copyright 2019 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "NFS-e (Nota Paulistana)",
    "summary": """
        NFS-e (Nota Paulistana)""",
    "version": "15.0.1.1.0",
    "license": "AGPL-3",
    "author": "KMEE, Odoo Community Association (OCA)",
    "maintainers": ["gabrielcardoso21", "mileo", "luismalta"],
    "development_status": "Beta",
    "website": "https://github.com/OCA/l10n-brazil",
    "external_dependencies": {
        "python": [
            "erpbrasil.edoc>=2.5.2",
            "erpbrasil.assinatura",
            "erpbrasil.transmissao>=1.1.0",
            "erpbrasil.base",
            "nfselib.paulistana",
            "unidecode",
        ],
    },
    "depends": [
        "l10n_br_nfse",
    ],
}
