# Copyright (C) 2026 - KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    "name": "Brazilian Payment Terms on Business Days",
    "summary": "Move a due date to the previous or next banking business day.",
    "category": "Localization",
    "license": "AGPL-3",
    "author": "KMEE,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-brazil",
    "development_status": "Beta",
    "maintainers": ["ygcarvalh"],
    "version": "18.0.1.0.0",
    "depends": ["account", "l10n_br_resource"],
    "data": ["views/account_payment_term_view.xml"],
    "installable": True,
}
