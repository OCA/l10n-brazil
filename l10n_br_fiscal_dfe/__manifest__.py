# Copyright 2023 KMEE
# Copyright 2026 Engenere
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Monitor de DF-e (Base)",
    "summary": """
    Abstract framework to monitor incoming electronic fiscal documents
    via the Sefaz DF-e distribution web service.
    """,
    "version": "16.0.1.2.0",
    "license": "AGPL-3",
    "author": "Engenere, KMEE, Odoo Community Association (OCA)",
    "maintainers": ["felipemotter", "antoniospneto", "rvalyi"],
    "website": "https://github.com/OCA/l10n-brazil",
    "depends": ["l10n_br_fiscal", "queue_job"],
    "data": [
        # Security
        "security/dfe_security.xml",
        "security/ir.model.access.csv",
        # Data
        "data/dfe_actions.xml",
        "data/queue_job_data.xml",  # Defines root.dfe channel
        # Views
        "views/dfe_banner_template.xml",
        "views/dfe_document_views.xml",
        "views/dfe_views.xml",
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
        ],
    },
}
