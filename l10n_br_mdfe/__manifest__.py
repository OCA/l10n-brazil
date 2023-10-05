# Copyright 2023 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "MDFe",
    "summary": """Brazilian Eletronic Invoice MDF-e""",
    "version": "14.0.1.0.0",
    "category": "Localisation",
    "license": "AGPL-3",
    "author": "KMEE,Odoo Community Association (OCA)",
    "maintainers": ["ygcarvalh"],
    "website": "https://github.com/OCA/l10n-brazil",
    "development_status": "Alpha",
    "depends": [
        "l10n_br_fiscal_certificate",
        "l10n_br_mdfe_spec",
        "spec_driven_model",
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/ir_config_parameter.xml",
        "views/document.xml",
        "views/mdfe_action.xml",
        "views/mdfe_menu.xml",
        "views/res_company.xml",
        "views/transporte.xml",
        "views/res_partner.xml",
        "views/product_product.xml",
        "views/modal/modal_aquaviario.xml",
        "views/modal/modal_rodoviario.xml",
        "views/modal/modal_ferroviario.xml",
    ],
    "demo": [
        "demo/fiscal_document_demo.xml",
        "demo/company_demo.xml",
    ],
    "post_init_hook": "post_init_hook",
    "installable": True,
    "auto_install": False,
    "external_dependencies": {
        "python": [
            "nfelib>=2.0.0",
            "erpbrasil.transmissao>=1.1.0",
            "erpbrasil.edoc>=2.5.2",
        ]
    },
}
