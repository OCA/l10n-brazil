# Copyright 2023 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Monitor de NF-e",
    "summary": """
    Monitor incoming NF-e documents via the DF-e distribution web service
    (NFeDistribuicaoDFe).
    """,
    "version": "16.0.1.4.0",
    "license": "AGPL-3",
    "author": "Engenere,KMEE,Odoo Community Association (OCA)",
    "maintainers": ["felipemotter", "antoniospneto"],
    "website": "https://github.com/OCA/l10n-brazil",
    "depends": ["l10n_br_nfe", "queue_job"],
    "data": [
        # Data
        "data/ir_cron.xml",
        "data/dfe_actions.xml",
        "data/queue_job_data.xml",
        # Security
        "security/dfe_security.xml",
        "security/ir.model.access.csv",
        # Views
        "views/dfe_banner_template.xml",
        "views/dfe_views.xml",
        "views/dfe_document_views.xml",
        "views/dfe_distribution_log_views.xml",
        "views/l10n_br_fiscal_menu.xml",
        "views/res_company_view.xml",
        "views/res_users_views.xml",
        # Wizards
        "wizards/specific_search_wizard.xml",
    ],
    "external_dependencies": {
        "python": [
            "brazil_fiscal_client",
            "nfelib",
        ],
    },
}
