# Copyright 2026 Escodoo
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Brazilian CBS Assisted Assessment Mock",
    "summary": "Local stand-in for the CBS assessment APIs, for demos and development",
    "version": "18.0.1.0.0",
    "license": "AGPL-3",
    "author": "Escodoo, Odoo Community Association (OCA)",
    "maintainers": ["marcelsavegnago"],
    "website": "https://github.com/OCA/l10n-brazil",
    "category": "Accounting",
    "development_status": "Alpha",
    "depends": ["l10n_br_cbs_assisted_assessment"],
    "data": [
        "security/cbs_assessment_mock_security.xml",
        "security/ir.model.access.csv",
        "views/res_company_view.xml",
        "views/assisted_assessment_view.xml",
        "views/mock_file_view.xml",
        "wizards/mock_generate_view.xml",
    ],
    "installable": True,
}
