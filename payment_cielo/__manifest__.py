# Copyright 2020 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Payent Cielo",
    "summary": """
        Payment Acquirer: Cielo Implementation""",
    "version": "16.0.1.0.0",
    "development_status": "Alpha",
    "license": "AGPL-3",
    "author": "KMEE INFORMATICA LTDA,Odoo Community Association (OCA)",
    "maintainers": ["DiegoParadeda"],
    "website": "https://github.com/OCA/l10n-brazil",
    "depends": ["payment"],
    "data": [
        # Views Templates
        "views/payment_cielo_templates.xml",
        # Data
        "data/payment_provider_data.xml",
        # Views
        "views/payment_provider_views.xml",
        "views/payment_icon_data.xml",
    ],
    "images": ["static/description/icon.png"],
    "installable": True,
    "post_init_hook": "post_init_hook",
    "uninstall_hook": "uninstall_hook",
}
