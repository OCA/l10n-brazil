# Copyright 2026 Akretion - Raphaël Valyi <raphael.valyi@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

"""Widen the bill line ``partner_order`` to 32 characters.

It is the stored related of ``l10n_br_fiscal.document.line.partner_order`` and
it carries the key the bill is reconciled against its receipt with; the column
was created at 15 and Odoo does not resize it when the source field grows.
"""


def migrate(cr, version):
    if not version:
        return
    cr.execute(
        """
        SELECT character_maximum_length
          FROM information_schema.columns
         WHERE table_name = 'account_move_line'
           AND column_name = 'partner_order'
        """
    )
    row = cr.fetchone()
    if row and row[0] and row[0] < 32:
        cr.execute(
            "ALTER TABLE account_move_line "
            "ALTER COLUMN partner_order TYPE varchar(32)"
        )
