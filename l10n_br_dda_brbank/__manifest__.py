# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "L10n Br DDA Brbank",
    "summary": "Feeds the DDA inbox from the API of the bank: webhook, "
    "incremental pull and daily reconciliation",
    "version": "18.0.1.0.0",
    "license": "AGPL-3",
    "author": "KMEE,Odoo Community Association (OCA)",
    "maintainers": ["mileo"],
    "website": "https://github.com/OCA/l10n-brazil",
    "development_status": "Beta",
    "category": "Accounting/Localizations",
    "depends": [
        "l10n_br_dda",
        "l10n_br_bank_connection",
    ],
    # Module name only: a version specifier here breaks the import check.
    "external_dependencies": {"python": ["brbank"]},
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "data/ir_cron.xml",
        "views/bank_connection_views.xml",
        "views/dda_event_views.xml",
    ],
    "demo": [
        "demo/connection_demo.xml",
    ],
}
