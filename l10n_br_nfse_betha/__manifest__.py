# Copyright 2022 Engenere
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    "name": "NFS-e (Betha)",
    "summary": """
        Emissão de NFS-e pelo provedor Betha""",
    "version": "14.0.1.0.0",
    "license": "AGPL-3",
    "author": "Engenere, Odoo Community Association (OCA)",
    "maintainers": ["antoniospneto", "felipemotter"],
    "website": "https://github.com/OCA/l10n-brazil",
    "development_status": "Beta",
    "external_dependencies": {
        "python": [
            "erpbrasil.edoc>=2.5.2",
            "erpbrasil.assinatura>=1.7.0",
            "erpbrasil.transmissao>=1.1.0",
            "erpbrasil.base>=2.3.0",
        ],
    },
    "depends": [
        "l10n_br_nfse",
    ],
}
