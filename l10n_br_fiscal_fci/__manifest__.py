# Copyright (C) 2026  Renato Lima - Akretion <renato.lima@akretion.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
{
    "name": "L10n BR Fiscal FCI",
    "summary": """FCI Management""",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "author": "Akretion,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-brazil",
    "depends": ["l10n_br_fiscal"],
    "data": [
        # Security
        "security/ir.model.access.csv",
        "security/l10n_br_fiscal_fci.xml",
        # Wizards
        "wizards/fci_import_wizard.xml",
        # Views
        "views/fci.xml",
        "views/fci_line.xml",
        "views/product_template.xml",
        # Actions
        "views/l10n_br_fiscal_fci_action.xml",
        # Menus
        "views/l10n_br_fiscal_fci_menu.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "l10n_br_fiscal_fci/static/src/components/**/*.js",
            "l10n_br_fiscal_fci/static/src/components/**/*.xml",
        ],
    },
    "installable": True,
}
