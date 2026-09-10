# Copyright 2023 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Payment Pix",
    "summary": """
        Payment Provider: Pix, through the API of the Central Bank""",
    "version": "16.0.1.0.0",
    "development_status": "Alpha",
    "license": "AGPL-3",
    "author": "KMEE,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-brazil",
    "depends": ["payment"],
    "data": [
        "views/payment_bacen_pix_templates.xml",
        "views/payment_provider_views.xml",
        "data/payment_icon_data.xml",
        "data/payment_provider_data.xml",
        "data/ir_cron.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "payment_bacen_pix/static/src/js/payment_status.js",
        ],
    },
    "demo": [],
    "installable": True,
    "uninstall_hook": "uninstall_hook",
}
