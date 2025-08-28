# Copyright (C) 2009  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    "name": "Brazilian Localization Sale",
    "category": "Localisation",
    "license": "AGPL-3",
    "author": "Akretion, " "Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-brazil",
    "version": "16.0.5.1.0",
    "depends": ["sale_management", "l10n_br_account"],
    "data": [
        # Data
        "data/company.xml",
        # Security
        "security/ir.model.access.csv",
        "security/l10n_br_sale_security.xml",
        # View
        "views/res_config_settings_view.xml",
        "views/res_company_view.xml",
        "views/sale_view.xml",
        # Report
        "report/sale_report_view.xml",
        "report/sale_report_templates.xml",
    ],
    "demo": [
        # Demo
        "demo/product.xml",
        "demo/company.xml",
        "demo/l10n_br_sale.xml",
    ],
    "installable": True,
    "auto_install": True,
    "post_init_hook": "post_init_hook",
    "development_status": "Beta",
    "maintainers": ["renatonlima", "rvalyi"],
}
