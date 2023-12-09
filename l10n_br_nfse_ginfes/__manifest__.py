# Copyright 2019 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "NFS-e (Ginfes)",
    "summary": """
        NFS-e (Ginfes)""",
    "version": "14.0.1.1.0",
    "license": "AGPL-3",
    "author": "KMEE, Odoo Community Association (OCA)",
    "maintainers": ["gabrielcardoso21", "mileo", "luismalta"],
    "website": "https://github.com/OCA/l10n-brazil",
    "development_status": "Beta",
    "external_dependencies": {
        "python": [
            "erpbrasil.edoc>=2.5.2",
            "erpbrasil.assinatura>=1.7.0",
            "erpbrasil.transmissao>=1.1.0",
            "erpbrasil.base>=2.3.0",
            "nfselib.ginfes",
        ],
    },
    "depends": [
        "l10n_br_nfse",
    ],
}
