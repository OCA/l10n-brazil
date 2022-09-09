# Copyright (C) 2018 KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    "name": "l10n_br_tef",
    "version": "14.0.1.0.0",
    "category": "Point Of Sale",
    "summary": "Manage Payment TEF device from POS",
    "author": "KMEE, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "website": "https://github.com/OCA/l10n-brazil",
    "depends": [
        "point_of_sale",
    ],
    "data": [
        "views/pos_config_view.xml",
        "views/pos_payment_method_view.xml",

        "views/pos_assets.xml",
    ],
    "qweb": ["static/src/xml/templates.xml"],
}
