# Copyright 2026 Akretion - Raphaël Valyi <raphael.valyi@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

"""Widen ``stock_move.partner_order`` to 32 characters.

``stock.move`` inherits the fiscal document line mixin, so it carries the same
(order, position) key; widening the mixin does not resize the existing column.
"""


def migrate(cr, version):
    if not version:
        return
    cr.execute(
        """
        SELECT character_maximum_length
          FROM information_schema.columns
         WHERE table_name = 'stock_move'
           AND column_name = 'partner_order'
        """
    )
    row = cr.fetchone()
    if row and row[0] and row[0] < 32:
        cr.execute("ALTER TABLE stock_move ALTER COLUMN partner_order TYPE varchar(32)")
