# Copyright 2020 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Payment PagSeguro",
    "summary": """Payment Acquirer: PagSeguro  Implementation""",
    "version": "14.0.1.0.10",
    "license": "AGPL-3",
    "author": "KMEE, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-brazil",
    "depends": [
        "sale",  # Used sale order in currency validation
        "web_tour",
        "website_sale",
    ],
    "data": [
        "views/payment_pagseguro_templates.xml",
        "data/payment_acquirer_data.xml",
        "views/payment_acquirer.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "/payment_pagseguro/static/src/js/pagseguro_tokenize_card.js",
            "/payment_pagseguro/static/src/js/pagseguro_tour.js",
        ],
    },
    "demo": [],
    "uninstall_hook": "uninstall_hook",
}
