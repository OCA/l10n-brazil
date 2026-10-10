# Copyright 2026 Escodoo
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Brazilian CBS Assisted Assessment Transport",
    "summary": "Receita Federal transport for the CBS assisted assessment APIs",
    "version": "18.0.1.0.0",
    "license": "AGPL-3",
    "author": "Escodoo, Odoo Community Association (OCA)",
    "maintainers": ["marcelsavegnago"],
    "website": "https://github.com/OCA/l10n-brazil",
    "category": "Accounting",
    "development_status": "Beta",
    "depends": [
        "l10n_br_assisted_assessment",
    ],
    "post_load": "post_load",
    "data": [
        "data/ir_cron.xml",
        "views/res_company_view.xml",
    ],
    "installable": True,
}
