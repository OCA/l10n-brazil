# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "L10n Br DDA Payment Schedule",
    "summary": "The DDA boleto linked to a vendor bill is the instrument of its "
    "payable item in the payment schedule",
    "version": "18.0.1.0.0",
    "license": "AGPL-3",
    "author": "KMEE,Odoo Community Association (OCA)",
    "maintainers": ["mileo"],
    "website": "https://github.com/OCA/l10n-brazil",
    "development_status": "Beta",
    "category": "Accounting/Localizations",
    "depends": ["l10n_br_dda", "l10n_br_payment_schedule"],
    "data": [
        "views/account_move_line_views.xml",
        "views/dda_debit_views.xml",
    ],
    "auto_install": True,
}
