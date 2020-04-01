# Copyright (C) 2009  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    "name": "Brazilian Localization Sale",
    "category": "Localisation",
    "license": "AGPL-3",
    "author":
        'Akretion, '
        'Odoo Community Association (OCA)',
    "website": "http://odoo-brasil.org",
    "version": "12.0.1.0.0",
    "depends": ["sale", "l10n_br_fiscal"],
    "data": [
        # Security
        "security/ir.model.access.csv",
        "security/l10n_br_sale_security.xml",

        # View
        "views/res_config_settings_view.xml",
        "views/res_company_view.xml",
        "views/sale_view.xml",

        # Report
        "report/sale_report_view.xml",
    ],
    "demo": [
        # Demo
        "demo/l10n_br_sale_demo.xml",
        "demo/l10n_br_sale_product_demo.xml",
    ],
    "installable": True,
    "auto_install": True,
    "development_status": "Production/Stable",
    "maintainers": ["renatonlima"],
}
