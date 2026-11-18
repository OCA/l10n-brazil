# Copyright 2026 PopSolutions
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Brazilian Localization Sale Loyalty",
    "summary": "Loyalty discount rewards as fiscal discount (vDesc) on the "
    "Brazilian invoice generated from the delivery",
    "version": "18.0.1.0.0",
    "license": "AGPL-3",
    "author": "PopSolutions, Odoo Community Association (OCA)",
    "maintainers": ["marcos-mendez"],
    "website": "https://github.com/OCA/l10n-brazil",
    "development_status": "Beta",
    "category": "Localization",
    "depends": [
        "l10n_br_sale_stock",
        "sale_loyalty",
        "sale_loyalty_order_line_link",
    ],
    "installable": True,
    "auto_install": True,
}
