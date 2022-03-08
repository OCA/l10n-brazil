# Copyright (C) 2022 - TODAY Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    "name": "Brazilian Localization Sales commissions",
    "summary": """Customization of Sales commissions
        module for implementations in Brazil.""",
    "category": "Localization",
    "license": "AGPL-3",
    "author": "Akretion, Odoo Community Association (OCA)",
    "maintainers": ["renatonlima"],
    "website": "https://github.com/OCA/l10n-brazil",
    "version": "12.0.1.0.0",
    "depends": [
        "sale_commission",
        "l10n_br_account",
    ],
    "data": [
        "views/sale_order.xml",
        "wizards/wizard_invoice.xml",
    ],
    "installable": True,
    "development_status": "Beta",
}
