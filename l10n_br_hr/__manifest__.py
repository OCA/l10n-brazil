# (c) 2014 Kmee - Luis Felipe Mileo <mileo@kmee.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    "name": "Brazilian Localization HR",
    "summary": "Brazilian Localization HR",
    "category": "Localization",
    "author": "KMEE, " "Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-brazil",
    "version": "16.0.1.0.3",
    "depends": ["hr", "l10n_br_base", "hr_employee_relative"],
    "data": [
        "data/l10n_br_hr.cbo.csv",
        "data/hr_deficiency_data.xml",
        "data/hr_ethnicity_data.xml",
        "security/ir.model.access.csv",
        "views/res_company_view.xml",
        "views/l10n_br_hr_cbo_view.xml",
        "views/hr_employee_view.xml",
        "views/hr_job_view.xml",
        "views/inherited_hr_contract.xml",
    ],
    "test": [],
    "installable": True,
    "auto_install": False,
    "license": "AGPL-3",
    "external_dependencies": {
        "python": [
            "erpbrasil.base>=2.3.0",
        ]
    },
}
