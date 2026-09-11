# Copyright 2026 Engenere
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Monitor de NF-e",
    "summary": """
    Monitor incoming NF-e documents via the DF-e distribution web service
    (NFeDistribuicaoDFe).
    """,
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "author": "Engenere, KMEE, Akretion, Odoo Community Association (OCA)",
    "maintainers": ["felipemotter", "antoniospneto", "rvalyi"],
    "website": "https://github.com/OCA/l10n-brazil",
    "depends": ["l10n_br_fiscal_dfe", "l10n_br_nfe"],
    "data": [
        # Data
        "data/ir_cron.xml",
        "data/queue_job_data.xml",
        # Views
        "views/nfe_dfe_views.xml",
        "views/res_company_view.xml",
    ],
    "external_dependencies": {
        "python": [
            "nfelib",
            "brazil_fiscal_client",
            "brazilfiscalreport",
        ],
    },
}
