# Copyright 2022 Engenere
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
# pylint: disable=pointless-statement
{
    "name": "Payment Instrument Data",
    "summary": """
        This module allows store payment instrument data, such as boleto and pix cobrança. """,
    "version": "14.0.0.0.1",
    "author": "Engenere, Odoo Community Association (OCA)",
    "maintainers": ["antoniospneto", "felipemotter"],
    "website": "https://github.com/OCA/l10n-brazil",
    "license": "AGPL-3",
    "depends": [
        "l10n_br_base",
        "l10n_br_account",
    ],
    "data": [
        "views/account_move_line.xml",
        "security/ir.model.access.csv",
        "views/menu.xml",
        "views/l10n_br_account_payment_instrument_view.xml",
    ],
    "demo": [],
}
