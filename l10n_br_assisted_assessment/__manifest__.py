# Copyright 2026 Escodoo
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Brazilian IBS/CBS Assisted Assessment",
    "summary": "Assisted assessment core: periods, deadlines and reconciliation",
    "version": "18.0.1.0.0",
    "license": "AGPL-3",
    "author": "Escodoo, Odoo Community Association (OCA)",
    "maintainers": ["marcelsavegnago"],
    "website": "https://github.com/OCA/l10n-brazil",
    "category": "Accounting",
    "development_status": "Beta",
    "depends": [
        "l10n_br_fiscal",
        "l10n_br_resource",
        "mail",
    ],
    "data": [
        "security/assisted_assessment_security.xml",
        "security/ir.model.access.csv",
        "data/ir_cron.xml",
        "views/assisted_assessment_bookkeeping_view.xml",
        "views/assisted_assessment_line_view.xml",
        "views/assisted_assessment_divergence_view.xml",
        "views/assisted_assessment_request_view.xml",
        "views/assisted_assessment_view.xml",
        "views/res_company_view.xml",
        "views/assisted_assessment_menu.xml",
    ],
    "installable": True,
}
