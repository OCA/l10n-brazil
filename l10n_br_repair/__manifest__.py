# Copyright 2020 - TODAY, Escodoo
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Brazilian Localization Repair",
    "summary": """
        Brazilian Localization Repair""",
    "version": "14.0.1.0.3",
    "category": "Localisation",
    "license": "AGPL-3",
    "author": "Escodoo, " "Odoo Community Association (OCA)",
    "maintainers": ["marcelsavegnago"],
    "development_status": "Alpha",
    "website": "https://github.com/OCA/l10n-brazil",
    "images": ["static/description/banner.png"],
    "depends": [
        "repair",
        "l10n_br_stock_account",
    ],
    "data": [
        "data/res_company.xml",
        "views/res_company.xml",
        "views/repair_order.xml",
        "views/repair_fee.xml",
        "views/repair_line.xml",
        "report/repair_templates_repair_order.xml",
    ],
    "demo": ["demo/res_company.xml", "demo/repair_order.xml"],
    "installable": True,
}
