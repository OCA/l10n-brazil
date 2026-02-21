# Copyright 2026 Engenere (<https://engenere.one>)
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
{
    "name": "DF-e Mock (SEFAZ Virtual)",
    "summary": "Mock SEFAZ DF-e distribution for development without A1 certificate.",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "author": "Engenere, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-brazil",
    "depends": ["l10n_br_fiscal_dfe"],
    "data": [
        # Security
        "security/dfe_mock_security.xml",
        "security/ir.model.access.csv",
        # Views
        "views/dfe_mock_banner_template.xml",
        "views/dfe_mock_nsu_views.xml",
        "views/res_company_view.xml",
        # Wizards
        "wizards/dfe_mock_generate_wizard.xml",
    ],
    "development_status": "Alpha",
}
