# Copyright 2020 - TODAY, Escodoo
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "NFS-e (ISSNet)",
    "summary": """
        NFS-e (ISSNet)""",
    "version": "12.0.3.1.0",
    "license": "AGPL-3",
    "author": "Escodoo, Odoo Community Association (OCA)",
    "maintainers": ["marcelsavegnago"],
    "website": "https://github.com/OCA/l10n-brazil",
    "images": ["static/description/banner.png"],
    "external_dependencies": {
        "python": [
            "erpbrasil.edoc",
            "erpbrasil.assinatura",
            "erpbrasil.transmissao",
            "erpbrasil.base",
            "nfselib.issnet",
        ],
    },
    "depends": [
        "l10n_br_nfse",
    ],
    "demo": [
        "demo/city_taxation_code_demo.xml",
    ],
}
