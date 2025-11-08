# Copyright 2023 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Monitor de NF-e",
    "summary": """
    Monitor incoming NF-e documents via the DF-e distribution web service
    (NFeDistribuicaoDFe).
    """,
    "version": "16.0.1.2.0",
    "license": "AGPL-3",
    "author": "KMEE,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-brazil",
    "depends": ["l10n_br_nfe"],
    "data": [
        # Data
        "data/ir_cron.xml",
        # Security
        "security/dfe_security.xml",
        "security/ir.model.access.csv",
        # Views
        "views/dfe_monitor_views.xml",
        "views/dfe_views.xml",
        "views/nfe_dfe_bundle_view.xml",
        "views/l10n_br_fiscal_menu.xml",
        "views/res_company_view.xml",
    ],
    "external_dependencies": {
        "python": [
            "nfelib",
        ],
    },
}
