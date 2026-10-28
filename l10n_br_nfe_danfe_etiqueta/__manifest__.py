# Copyright 2026 PopSolutions
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "DANFE Simplificado - Etiqueta",
    "summary": "Print the NF-e shipping label (DANFE Simplificado - Etiqueta)",
    "category": "Localisation",
    "license": "AGPL-3",
    "author": "PopSolutions, Odoo Community Association (OCA)",
    "maintainers": ["marcos-mendez"],
    "website": "https://github.com/OCA/l10n-brazil",
    "development_status": "Beta",
    "version": "18.0.1.0.0",
    "depends": [
        "l10n_br_nfe",
    ],
    "data": [
        "views/danfe_profile_view.xml",
        "report/danfe_etiqueta_report.xml",
    ],
    "installable": True,
    "external_dependencies": {
        "python": [
            "brazilfiscalreport>=1.3.1",
        ],
    },
}
