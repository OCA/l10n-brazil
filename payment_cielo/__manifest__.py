# Copyright 2020 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Payment Cielo",
    "summary": """
        Payment Provider: Cielo Implementation""",
    "version": "16.0.1.0.0",
    "development_status": "Alpha",
    "license": "AGPL-3",
    "author": "KMEE INFORMATICA LTDA,Odoo Community Association (OCA)",
    "maintainers": ["DiegoParadeda"],
    "website": "https://github.com/OCA/l10n-brazil",
    "depends": ["payment"],
    "data": [
        "views/payment_cielo_templates.xml",
        "views/payment_provider_views.xml",
        "data/payment_icon_data.xml",
        "data/payment_provider_data.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "payment_cielo/static/src/js/payment_form.js",
        ],
    },
    "images": ["static/description/icon.png"],
    "installable": True,
    "uninstall_hook": "uninstall_hook",
}
