# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Melhor Envio Shipping",
    "summary": "Shipping quotes, labels and tracking through Melhor Envio",
    "category": "Delivery",
    "license": "AGPL-3",
    "author": "KMEE, Odoo Community Association (OCA)",
    "maintainers": ["mileo"],
    "website": "https://github.com/OCA/l10n-brazil",
    "development_status": "Beta",
    "version": "18.0.1.0.0",
    "depends": [
        "delivery_state",
        "l10n_br_base",
        "l10n_br_account",
    ],
    "data": [
        "security/ir.model.access.csv",
        "security/melhorenvio_security.xml",
        "data/product_product_data.xml",
        "views/melhorenvio_account_views.xml",
        "views/delivery_carrier_view.xml",
        "views/stock_picking_view.xml",
    ],
    "installable": True,
}
