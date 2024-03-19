# Copyright 2019 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "L10n Br Portal",
    "summary": """
        Campos Brasileiros no Portal""",
    "version": "14.0.2.0.1",
    "license": "AGPL-3",
    "author": "KMEE,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-brazil",
    "development_status": "Beta",
    "depends": [
        "portal",
        "l10n_br_zip",
    ],
    "demo": [
        "demo/res_users_demo.xml",
    ],
    "data": [
        "views/assets.xml",
        "views/portal_templates.xml",
    ],
    "auto_install": True,
}
