# Copyright 2023 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "L10n Br Fiscal Purchase",
    "summary": """
        Fiscal Purchase""",
    "version": "14.0.1.0.0",
    "license": "AGPL-3",
    "author": "KMEE,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-brazil",
    "depends": [
        "l10n_br_fiscal",
        "l10n_br_purchase",
    ],
    "data": [
        "views/document_view.xml",
        "views/purchase_order_view.xml",
    ],
}
