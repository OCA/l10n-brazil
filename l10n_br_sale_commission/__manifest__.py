# Copyright (C) 2022 - TODAY Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    "name": "Brazilian Localization Sales Commissions",
    "summary": """Brazilian Localization of Sales Commissions""",
    "category": "Localization",
    "license": "AGPL-3",
    "author": "Akretion, Odoo Community Association (OCA)",
    "maintainers": ["renatonlima"],
    "website": "https://github.com/OCA/l10n-brazil",
    "version": "16.0.1.2.0",
    "depends": [
        "sale_commission",
        "l10n_br_sale",
    ],
    "data": [
        "views/res_config_settings_views.xml",
        "wizards/wizard_invoice.xml",
    ],
    "demo": ["demo/res_config_settings_demo.xml", "demo/sale_order_demo.xml"],
    "installable": True,
    "development_status": "Beta",
}
