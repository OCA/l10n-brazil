# Copyright (C) 2016  Daniel Sadamo - KMEE Informática
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    "name": "Brazilian Localization HR Contract",
    "category": "Localisation",
    "license": "AGPL-3",
    "author": "KMEE, " "Odoo Community Association (OCA)",
    "website": "http://odoo-brasil.org",
    "version": "12.0.1.0.0",
    "depends": ["hr_contract", "l10n_br_hr"],
    "data": [
        "views/hr_contract_view.xml",
        "data/l10n_br_hr_contract_data.xml",
        "data/l10n_br_hr_contract_resignation_data.xml",
        "security/ir.model.access.csv",
    ],
    "test": [],
    "external_dependencies": {"python": ["erpbrasil.base.fiscal"]},
    "installable": True,
    "auto_install": False,
}
