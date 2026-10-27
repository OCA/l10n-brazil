# Copyright (C) 2026 - Luis Felipe Mileo - KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Brazilian Fiscal Spreadsheet Dashboards",
    "summary": "Spreadsheet dashboards over the fiscal document lines analysis",
    "version": "18.0.1.0.0",
    "category": "Localisation",
    "license": "AGPL-3",
    "author": "KMEE, Odoo Community Association (OCA)",
    "maintainers": ["mileo"],
    "website": "https://github.com/OCA/l10n-brazil",
    "development_status": "Beta",
    "depends": [
        "l10n_br_fiscal",
        "spreadsheet_dashboard",
    ],
    "data": [
        "data/dashboards.xml",
    ],
    "installable": True,
}
