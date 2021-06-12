# Copyright 2020 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Brazilian Localization Contract",
    "summary": """
        Customization of Contract module for implementations in Brazil.""",
    "version": "12.0.4.1.0",
    "license": "AGPL-3",
    "author": "KMEE,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-brazil",
    "depends": ["l10n_br_account", "contract"],
    "data": [
        "data/company.xml",
        "views/res_company.xml",
        "views/contract_view.xml",
        "views/contract_line.xml",
    ],
    "demo": [
        "demo/company.xml",
        "demo/contract_demo.xml",
    ],
}
