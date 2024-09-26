# Copyright 2024 - TODAY, Escodoo
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Brazilian Localization Expense Invoice",
    "summary": """
        Customization of HR Expense Invoice module for implementations in Brazil.""",
    "version": "14.0.1.0.1",
    "license": "AGPL-3",
    "author": "Escodoo,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-brazil",
    "depends": [
        "l10n_br_fiscal",
        "hr_expense_invoice",
    ],
    "data": [
        "views/hr_expense_sheet.xml",
        "views/res_company.xml",
    ],
}
