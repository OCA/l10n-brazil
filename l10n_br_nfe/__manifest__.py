# Copyright (C) 2019  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html


{
    "name": "NF-e",
    "summary": "Eletronic Invoicing for Brazil / NF-e",
    "category": "Localisation",
    "license": "AGPL-3",
    "author": "Akretion," "KMEE," "Odoo Community Association (OCA)",
    "maintainers": ["rvalyi", "renatonlima"],
    "website": "https://github.com/OCA/l10n-brazil",
    "development_status": "Beta",
    "version": "14.0.17.1.1",
    "depends": [
        "l10n_br_fiscal_edi",
        "l10n_br_fiscal_certificate",
        "l10n_br_nfe_spec",
        "spec_driven_model",
        "l10n_br_fiscal_dfe",
    ],
    "data": [
        # Data
        "data/ir_config_parameter.xml",
        # Security
        "security/nfe_security.xml",
        "security/ir.model.access.csv",
        # Views
        "views/res_company_view.xml",
        "views/nfe_document_view.xml",
        "views/res_config_settings_view.xml",
        "views/mde/mde_views.xml",
        "views/dfe/dfe_views.xml",
        "views/supplier_info_view.xml",
        # Report
        "report/reports.xml",
        "report/danfe_nfce.xml",
        "report/danfe_report.xml",
        # Wizards
        "wizards/import_document.xml",
        # Actions,
        "views/nfe_action.xml",
        # Menus
        "views/nfe_menu.xml",
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
            "nfelib<=2.0.7",
            "erpbrasil.assinatura>=1.7.0",
            "erpbrasil.transmissao>=1.1.0",
            "erpbrasil.edoc>=2.5.2",
            "erpbrasil.edoc.pdf",
            "erpbrasil.base>=2.3.0",
            "brazilfiscalreport",
        ],
    },
}
