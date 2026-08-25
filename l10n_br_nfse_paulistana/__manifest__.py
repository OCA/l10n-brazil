# Copyright 2019 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "NFS-e (Nota Paulistana)",
    "summary": """
        NFS-e (Nota Paulistana)""",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "author": "KMEE, Odoo Community Association (OCA)",
    "maintainers": ["gabrielcardoso21", "mileo", "luismalta", "CristianoMafraJunior"],
    "development_status": "Beta",
    "website": "https://github.com/OCA/l10n-brazil",
    "external_dependencies": {
        "python": [
            "erpbrasil.edoc",
            "erpbrasil.assinatura",
            "erpbrasil.transmissao",
            "erpbrasil-base>=2.4.2",
            "nfselib.paulistana",
            "unidecode",
        ],
    },
    "data": [
        "views/document_view.xml",
    ],
    "depends": [
        "l10n_br_nfse",
    ],
}
