# Copyright 2026 - TODAY, Escodoo
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Brazilian Localization Purchase Blanket Order",
    "summary": """
        Brazilian Localization Purchase Blanket Order""",
    "version": "18.0.1.1.0",
    "license": "AGPL-3",
    "author": "Escodoo, Odoo Community Association (OCA)",
    "maintainers": ["WesleyOliveira98", "marcelsavegnago"],
    "website": "https://github.com/OCA/l10n-brazil",
    "depends": ["purchase_blanket_order", "l10n_br_purchase"],
    "data": [
        "views/purchase_blanket_order.xml",
        "views/purchase_blanket_order_line.xml",
    ],
    "installable": True,
    "auto_install": False,
}
