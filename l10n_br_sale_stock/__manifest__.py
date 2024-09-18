# Copyright (C) 2013  Raphaël Valyi - Akretion
# Copyright (C) 2013  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    "name": "Brazilian Localization Sales and Warehouse",
    "category": "Localization",
    "license": "AGPL-3",
    "author": "Akretion, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-brazil",
    "version": "15.0.1.0.0",
    "development_status": "Beta",
    "maintainers": ["renatonlima", "mbcosta"],
    "depends": [
        "sale_stock_picking_invoicing",
        "l10n_br_sale",
        "l10n_br_stock_account",
    ],
    "demo": [
        "demo/l10n_br_sale_stock_demo.xml",
        "demo/sale_order_demo.xml",
    ],
    "installable": True,
    "auto_install": True,
}
