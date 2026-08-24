# Copyright 2025 Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Brazilian Account Installment Renegotiation",
    "summary": "Allows renegotiating payment installments on posted invoices in Brazil",
    "version": "16.0.1.0.1",
    "category": "Localization",
    "license": "AGPL-3",
    "author": "Akretion, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-brazil",
    "maintainers": ["rvalyi"],
    "development_status": "Beta",
    "depends": [
        "account_payment_partner",
    ],
    "data": [
        "security/ir.model.access.csv",
        "wizards/installment_renegotiation_wizard_views.xml",
        "views/account_move_views.xml",
    ],
    "installable": True,
    "auto_install": False,
}
