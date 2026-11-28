# Copyright 2026 PopSolutions
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Brazilian Localization - PPE Certificate of Approval (CAEPI)",
    "summary": "Automatic CA lookup from the MTE public database",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "author": "PopSolutions, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-brazil",
    "category": "Localization",
    "depends": [
        "hr_employee_ppe",
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/ir_cron.xml",
        "views/product_template_views.xml",
        "views/caepi_certificate_views.xml",
    ],
    "installable": True,
}
