# Copyright (C) 2009  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    "name": "Brazilian Localization Purchase",
    "license": "AGPL-3",
    "category": "Localisation",
    "author": "Akretion, Odoo Community Association (OCA)",
    "maintainers": ["renatonlima", "rvalyi"],
    "website": "https://github.com/OCA/l10n-brazil",
    "version": "16.0.1.0.0",
    "depends": ["purchase", "l10n_br_account"],
    "data": [
        # Security
        "security/ir.model.access.csv",
        # Data
        "data/company.xml",
        # View
        "views/purchase_view.xml",
        "views/res_company_view.xml",
        # Reports
        "reports/purchase_report_views.xml",
        #        "reports/purchase_order_templates.xml",
    ],
    "demo": [
        "demo/company.xml",
        "demo/product.xml",
        "demo/l10n_br_purchase.xml",
    ],
    "installable": True,
    "post_init_hook": "post_init_hook",
    "auto_install": False,
}
