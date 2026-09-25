# Copyright 2020 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Payment PagSeguro",
    "summary": """Payment Provider: PagSeguro (PagBank) Implementation""",
    "version": "16.0.1.0.0",
    "development_status": "Alpha",
    "license": "AGPL-3",
    "author": "KMEE, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-brazil",
    "depends": ["payment"],
    "data": [
        "views/payment_pagseguro_templates.xml",
        "views/payment_provider_views.xml",
        "data/payment_provider_data.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "payment_pagseguro/static/src/js/payment_form.js",
        ],
    },
    "demo": [],
    "installable": True,
    "uninstall_hook": "uninstall_hook",
}
