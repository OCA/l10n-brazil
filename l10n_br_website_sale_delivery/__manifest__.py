# Copyright 2020 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Brazilian Localization Website Sale Delivery",
    "summary": """
        Implements Brazilian freight values for delivery.""",
    "version": "14.0.1.0.1",
    "license": "AGPL-3",
    "author": "KMEE,Odoo Community Association (OCA)",
    "development_status": "Alpha",
    "maintainers": ["marcelsavegnago", "DiegoParadeda"],
    "website": "https://github.com/OCA/l10n-brazil",
    "depends": [
        "website_sale_delivery",
        "l10n_br_delivery",
        "l10n_br_website_sale",
    ],
    "assets": {
        "web.assets_frontend": [
            "/l10n_br_website_sale_delivery/static/src/js/l10n_br_website_sale_delivery_tour.js",
        ],
    },
    "category": "Localization",
    "installable": True,
}
