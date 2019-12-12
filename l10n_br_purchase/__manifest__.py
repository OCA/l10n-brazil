# Copyright (C) 2009  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    "name": "Brazilian Localization Purchase",
    "license": "AGPL-3",
    "category": "Localisation",
    "author": "Akretion, Odoo Community Association (OCA)",
    "website": "http://odoo-brasil.org",
    "version": "12.0.1.0.0",
    "depends": ["purchase", "l10n_br_account", "l10n_br_fiscal"],
    "data": [
        # Security
        "security/ir.model.access.csv",
        # Data
        "data/l10n_br_purchase_data.xml",
        # View
        "views/purchase_view.xml",
        "views/res_company_view.xml",
    ],
    "demo": ["demo/l10n_br_purchase_demo.xml"],
    "installable": True,
    "auto_install": False,
}
