# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "L10n Br Bank Connection",
    "summary": "Shared connection to a Brazilian bank: credentials, token, "
    "OAuth consent and webhook",
    "version": "18.0.1.0.0",
    "license": "AGPL-3",
    "author": "KMEE,Odoo Community Association (OCA)",
    "maintainers": ["mileo"],
    "website": "https://github.com/OCA/l10n-brazil",
    "development_status": "Beta",
    "depends": [
        "account",
        "mail",
    ],
    # Module name only: a version specifier here breaks the import check.
    "external_dependencies": {"python": ["brbank"]},
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "views/connection_views.xml",
    ],
    "demo": [
        "demo/connection_demo.xml",
    ],
}
