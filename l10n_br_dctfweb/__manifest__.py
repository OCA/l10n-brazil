# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
{
    "name": "DCTFWeb/MIT (Brazil)",
    "summary": "Assess the federal debits of the MIT and build its JSON file",
    "version": "16.0.1.0.0",
    "category": "Localization/Brazil",
    "license": "AGPL-3",
    "author": "KMEE, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-brazil",
    "development_status": "Alpha",
    "maintainers": ["mileo"],
    "depends": [
        "l10n_br_tax_assessment",
    ],
    "data": [
        "security/dctfweb_security.xml",
        "security/ir.model.access.csv",
        "data/l10n_br_dctfweb.revenue.code.csv",
        "views/dctfweb_revenue_code_views.xml",
        "views/dctfweb_assessment_views.xml",
        "views/res_company_views.xml",
        "views/account_tax_group_views.xml",
    ],
    "demo": [
        "demo/dctfweb_demo.xml",
    ],
    "installable": True,
}
