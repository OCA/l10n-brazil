# Copyright 2020 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "L10n Br Website Sale OCA",
    "summary": """
        Website sale localização brasileira.""",
    "version": "18.0.1.0.0",
    "development_status": "Beta",
    "license": "AGPL-3",
    "author": "KMEE, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-brazil",
    "depends": [
        "website_sale",
        "l10n_br_sale",
        "l10n_br_portal",
        "payment",
    ],
    "data": [
        "templates/portal_templates.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "/l10n_br_website_sale_oca/static/src/js/l10n_br_address.esm.js",
        ],
        "web.assets_tests": [
            "/l10n_br_website_sale_oca/static/src/js/l10n_br_website_sale_oca_tour.esm.js",
        ],
    },
    "external_dependencies": {
        "python": [
            "erpbrasil-base>=2.4.2",
        ]
    },
}
