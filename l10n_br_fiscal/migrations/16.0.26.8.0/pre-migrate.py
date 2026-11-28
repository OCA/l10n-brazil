# Copyright 2026 Akretion - Raphaël Valyi <raphael.valyi@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

"""Widen ``partner_order`` from 15 to 32 characters.

The field is the (order, position) key a vendor bill is reconciled against its
receipt with, and Odoo does not alter an existing column when a ``Char`` size
grows: without this the column stays at 15 and every reference longer than that
either fails or is truncated, which is exactly what makes two orders of the same
decade share a key.

The NF-e layout still caps xPed at 15 characters, so only the storage grows: an
outgoing document keeps respecting the layout.
"""


def migrate(cr, version):
    if not version:
        return
    cr.execute(
        """
        SELECT character_maximum_length
          FROM information_schema.columns
         WHERE table_name = 'l10n_br_fiscal_document_line'
           AND column_name = 'partner_order'
        """
    )
    row = cr.fetchone()
    if row and row[0] and row[0] < 32:
        cr.execute(
            "ALTER TABLE l10n_br_fiscal_document_line "
            "ALTER COLUMN partner_order TYPE varchar(32)"
        )
