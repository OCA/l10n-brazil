# Copyright 2026 Escodoo
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Monitor de NFS-e",
    "summary": """
    Monitor incoming national NFS-e documents via the ADN distribution API.
    """,
    "version": "18.0.1.0.0",
    "license": "AGPL-3",
    "author": "Escodoo, Odoo Community Association (OCA)",
    "maintainers": ["marcelsavegnago"],
    "website": "https://github.com/OCA/l10n-brazil",
    "development_status": "Alpha",
    "depends": [
        "l10n_br_fiscal_dfe",
        "l10n_br_nfse",
        "l10n_br_fiscal_certificate",
    ],
    "data": [
        "data/ir_cron.xml",
        "views/res_company_view.xml",
        "views/nfse_dfe_views.xml",
        "wizards/document_import_wizard.xml",
    ],
    "external_dependencies": {
        "python": [
            "requests",
            "cryptography",
        ],
    },
    "installable": True,
}
