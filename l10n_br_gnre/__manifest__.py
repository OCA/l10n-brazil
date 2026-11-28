# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "GNRE",
    "summary": """Guia Nacional de Recolhimento de Tributos Estaduais""",
    "version": "16.0.1.0.0",
    "category": "Localisation",
    "license": "AGPL-3",
    "author": "KMEE,Odoo Community Association (OCA)",
    "maintainers": ["mileo"],
    "website": "https://github.com/OCA/l10n-brazil",
    "development_status": "Alpha",
    "depends": [
        "l10n_br_fiscal_certificate",
        "l10n_br_fiscal_edi",
        "l10n_br_gnre_spec",
        "spec_driven_model",
    ],
    "external_dependencies": {
        "python": ["nfelib"],
    },
    "data": [
        "security/ir.model.access.csv",
        "data/ir_cron.xml",
        "views/res_company.xml",
        "views/document.xml",
        "views/gnre_state_config.xml",
        "views/gnre_obligation.xml",
        "wizards/gnre_generate_wizard.xml",
        "views/gnre_menu.xml",
    ],
    "installable": True,
}
