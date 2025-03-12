# Copyright 2023 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "CT-e",
    "summary": """Brazilian Electronic Invoice CT-e""",
    "version": "15.0.1.0.0",
    "category": "Localisation",
    "license": "AGPL-3",
    "author": "KMEE, Escodoo, Odoo Community Association (OCA)",
    "maintainers": ["mileo", "marcelsavegnago"],
    "website": "https://github.com/OCA/l10n-brazil",
    "development_status": "Alpha",
    "depends": [
        "l10n_br_fiscal_edi",
        "l10n_br_cte_spec",
        "l10n_br_fiscal_certificate",
        "spec_driven_model",
    ],
    "data": [
        # Data
        "data/ir_config_parameter.xml",
        # Security
        "security/ir.model.access.csv",
        # Views
        "views/document.xml",
        "views/res_company.xml",
        "views/modal/modal_rodoviario.xml",
        "views/modal/modal_aquaviario.xml",
        "views/modal/modal_ferroviario.xml",
        "views/modal/modal_aereo.xml",
        # Report
        "report/dacte_report.xml",
        # Wizards
        "wizards/document_correction_wizard.xml",
        # Actions
        "views/cte_action.xml",
    ],
    "demo": [
        "demo/company_demo.xml",
        "demo/fiscal_document_demo.xml",
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
        ],
    },
}
