# Copyright (C) 2018 KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    "name": "l10n_br_tef",
    "version": "12.0.1.0.0",
    "category": "Point Of Sale",
    "summary": "Manage Payment TEF device from POS",
    "author": "KMEE, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "website": "https://github.com/OCA/l10n-brazil",
    "depends": ["point_of_sale"],
    "data": [
        "data/account_journal_data.xml",
        "views/l10n_br_tef_view.xml",
        "views/pos_assets.xml",
        "views/account_journal_view.xml",
    ],
    "demo": [
        "demo/l10n_br_tef_demo.xml",
    ],
    "qweb": ["static/src/xml/templates.xml"],
}
