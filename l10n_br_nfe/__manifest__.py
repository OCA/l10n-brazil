# Copyright (C) 2019  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    "name": "NF-e",
    "summary": "Brazilian Eletronic Invoice NF-e .",
    "category": "Localisation",
    "license": "AGPL-3",
    "author": "Akretion," "KMEE," "Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-brazil",
    "development_status": "Beta",
    "version": "12.0.6.0.0",
    "depends": [
        "l10n_br_fiscal",
        "l10n_br_nfe_spec",
        "spec_driven_model",
    ],
    "data": [
        # Data
        "data/ir_config_parameter.xml",
        # Security
        "security/nfe_security.xml",
        # Views
        "views/res_company_view.xml",
        "views/nfe_document_view.xml",
        "views/res_config_settings_view.xml",
    ],
    "demo": [
        "demo/res_users_demo.xml",
        "demo/fiscal_document_demo.xml",
        "demo/company_demo.xml",
    ],
    "post_init_hook": "post_init_hook",
    "installable": True,
    "auto_install": False,
    "external_dependencies": {
        "python": [
            "nfelib",
            "erpbrasil.base",
            "erpbrasil.assinatura",
            "erpbrasil.transmissao",
            "erpbrasil.edoc",
            "erpbrasil.edoc.pdf",
            "xmldiff",
        ],
    },
}
