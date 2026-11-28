# Copyright 2020 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Brazilian Localization Website Sale Delivery",
    "summary": """
        Implements Brazilian freight values for delivery.""",
    "version": "18.0.1.0.0",
    "license": "AGPL-3",
    "author": "KMEE,Odoo Community Association (OCA)",
    "development_status": "Alpha",
    "maintainers": ["marcelsavegnago", "DiegoParadeda"],
    "website": "https://github.com/OCA/l10n-brazil",
    "depends": [
        "website_sale",
        "l10n_br_delivery",
        "l10n_br_website_sale_oca",
    ],
    "assets": {
        "web.assets_tests": [
            "l10n_br_website_sale_delivery/static/src/js/"
            "l10n_br_website_sale_delivery_tour.esm.js",
        ],
    },
    "demo": [],
    "category": "Localization",
    "installable": True,
}
