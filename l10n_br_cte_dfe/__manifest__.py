# Copyright 2026 Engenere
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Monitor de CT-e",
    "summary": """
    Monitor incoming CT-e documents via the DF-e distribution web service
    (CTeDistribuicaoDFe).
    """,
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "author": "Engenere, Odoo Community Association (OCA)",
    "maintainers": ["antoniospneto"],
    "website": "https://github.com/OCA/l10n-brazil",
    "development_status": "Beta",
    "depends": ["l10n_br_fiscal_dfe", "l10n_br_cte"],
    "data": [
        # Data
        "data/ir_cron.xml",
        # Views
        "views/cte_dfe_views.xml",
        "views/res_company_view.xml",
        "wizards/specific_search_wizard.xml",
    ],
    "external_dependencies": {
        "python": [
            "nfelib>=3.3.0",
            "brazil_fiscal_client",
            "brazilfiscalreport",
        ],
    },
}
