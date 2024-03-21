# Copyright 2017 Akretion
# @author Raphaël Valyi <raphael.valyi@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "L10n Br Account Payment BRCobranca",
    "version": "14.0.2.0.3",
    "license": "AGPL-3",
    "author": "Akretion, " "Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-brazil",
    "depends": [
        "l10n_br_account_payment_order",
        "account_move_base_import",
    ],
    "data": [
        # Security
        "security/ir.model.access.csv",
        # Views
        "views/account_move_view.xml",
        "views/account_journal_view.xml",
        # Wizard
        "wizard/import_statement_view.xml",
    ],
    "demo": [
        "demo/account_journal_demo.xml",
        "demo/account_move_demo.xml",
        "demo/account_payment_mode.xml",
    ],
}
