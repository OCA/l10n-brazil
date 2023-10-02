# Copyright (C) 2019  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    "name": "NF-e",
    "summary": "Brazilian Eletronic Invoice NF-e",
    "category": "Localisation",
    "license": "AGPL-3",
    "author": "Akretion," "KMEE," "Odoo Community Association (OCA)",
    "maintainers": ["rvalyi", "renatonlima"],
    "website": "https://github.com/OCA/l10n-brazil",
    "development_status": "Beta",
    "version": "14.0.13.4.0",
    "depends": [
        "l10n_br_fiscal",
        "l10n_br_fiscal_certificate",
        "l10n_br_nfe_spec",
        "spec_driven_model",
        "l10n_br_fiscal_dfe",
    ],
    "data": [
        # Data
        "data/ir_config_parameter.xml",
        # Security
        "security/ir_model_access.xml",
        "security/nfe_security.xml",
        # Views
        "views/res_company_view.xml",
        "views/nfe_document_view.xml",
        "views/res_config_settings_view.xml",
        "views/mde/mde_views.xml",
        "views/dfe/dfe_views.xml",
        # Report
        "report/reports.xml",
        "report/danfe_nfce.xml",
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
            "nfelib>=2.0.0",
            "erpbrasil.assinatura>=1.7.0",
            "erpbrasil.transmissao>=1.1.0",
            "erpbrasil.edoc>=2.5.2",
            "erpbrasil.edoc.pdf",
        ],
    },
}
