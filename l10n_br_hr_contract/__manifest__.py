# Copyright (C) 2016  Daniel Sadamo - KMEE Informática
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    "name": "Brazilian Localization HR Contract",
    "category": "Localisation",
    "license": "AGPL-3",
    "author": "KMEE, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-brazil",
    "version": "16.0.1.1.0",
    "depends": ["hr_contract", "l10n_br_hr"],
    "data": [
        # Data
        "data/hr_contract_admission_type_data.xml",
        "data/hr_contract_labor_bond_type_data.xml",
        "data/hr_contract_labor_regime_data.xml",
        "data/hr_contract_notice_termination_data.xml",
        "data/hr_contract_resignation_cause_data.xml",
        "data/hr_contract_salary_unit_data.xml",
        # Security
        "security/ir.model.access.csv",
        # Views
        "views/hr_contract_view.xml",
        # Action
        "views/l10n_br_hr_contract_action.xml",
        # Menu
        "views/l10n_br_hr_contract_menu.xml",
    ],
    "external_dependencies": {"python": ["erpbrasil.base>=2.3.0"]},
    "installable": True,
    "auto_install": False,
}
