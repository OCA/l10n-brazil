# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "NFS-e (GissOnline)",
    "summary": "NFS-e pelo webservice do GissOnline, versão 2",
    "version": "18.0.1.0.0",
    "license": "AGPL-3",
    "author": "KMEE, Odoo Community Association (OCA)",
    "maintainers": ["mileo"],
    "development_status": "Alpha",
    "website": "https://github.com/OCA/l10n-brazil",
    "external_dependencies": {
        "python": [
            "erpbrasil.edoc>=3.3.0",
            "erpbrasil.assinatura",
            "erpbrasil.transmissao",
            "erpbrasil-base>=2.4.2",
            "nfselib.giss",
        ],
    },
    "data": [
        "views/res_company_view.xml",
        "views/document_view.xml",
    ],
    "depends": [
        "l10n_br_nfse",
    ],
}
