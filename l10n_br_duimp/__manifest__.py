# Copyright (C) 2026 - TODAY, Escodoo
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    "name": "DUIMP Integration",
    "summary": "Import DUIMP (Import Declaration) data from the Portal "
    "Único Siscomex API and generate the vendor bill",
    "category": "Localisation",
    "license": "AGPL-3",
    "author": "Escodoo, Odoo Community Association (OCA)",
    "maintainers": ["kaynnan", "marcelsavegnago"],
    "website": "https://github.com/OCA/l10n-brazil",
    "version": "16.0.1.0.0",
    "development_status": "Alpha",
    "depends": [
        "l10n_br_account",
        "l10n_br_fiscal_certificate",
    ],
    "external_dependencies": {
        "python": [
            "erpbrasil.assinatura",
        ]
    },
    "data": [
        "security/ir.model.access.csv",
        "views/res_company_view.xml",
        "wizards/duimp_import_wizard_view.xml",
        "wizards/duimp_search_wizard_view.xml",
    ],
    "installable": True,
    "auto_install": False,
}
