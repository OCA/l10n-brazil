# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
{
    "name": "DCTFWeb/MIT transmission through the Serpro (Brazil)",
    "summary": "Close the MIT, transmit the DCTFWeb and issue its DARF",
    "version": "16.0.1.0.0",
    "category": "Localization/Brazil",
    "license": "AGPL-3",
    "author": "KMEE, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-brazil",
    "development_status": "Alpha",
    "maintainers": ["mileo"],
    "depends": [
        "l10n_br_dctfweb",
        "l10n_br_fiscal_certificate",
    ],
    "data": [
        "security/ir.model.access.csv",
        "security/dctfweb_serpro_security.xml",
        "wizards/dctfweb_cost_warning_views.xml",
        "views/dctfweb_transmission_views.xml",
        "views/dctfweb_assessment_views.xml",
        "views/res_company_views.xml",
    ],
    "external_dependencies": {
        "python": [
            "erpbrasil.assinatura",
        ]
    },
    "installable": True,
}
