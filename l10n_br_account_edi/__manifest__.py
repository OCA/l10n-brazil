# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Fiscal Document EDI: Invoicing",
    "summary": "Vendor bill of an imported fiscal document and the installments "
    "and payments of an issued one",
    "category": "Localisation",
    "license": "AGPL-3",
    "author": "KMEE, Odoo Community Association (OCA)",
    "maintainers": ["mileo"],
    "website": "https://github.com/OCA/l10n-brazil",
    "development_status": "Beta",
    "version": "16.0.1.0.0",
    "depends": [
        "l10n_br_account",
        "l10n_br_fiscal_edi",
    ],
    "data": [
        "views/document_view.xml",
        "views/account_move_view.xml",
    ],
    "installable": True,
    "auto_install": True,
}
