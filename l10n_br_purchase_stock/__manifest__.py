# Copyright (C) 2009  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    "name": "Brazilian Localization Purchase Stock",
    "license": "AGPL-3",
    "category": "Localisation",
    "author": "Akretion, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-brazil",
    "version": "12.0.2.0.0",
    "depends": [
        "l10n_br_purchase",
        "l10n_br_stock_account",
    ],
    "data": [
        # Views
        "views/purchase_order.xml",
        "views/res_config_settings.xml",
        "views/res_company_view.xml",
    ],
    "demo": [
        "demo/purchase_order.xml",
    ],
    "installable": True,
    "auto_install": True,
}
