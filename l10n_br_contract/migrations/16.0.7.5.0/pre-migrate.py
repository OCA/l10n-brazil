# Copyright 2026 Akretion - Raphaël Valyi <raphael.valyi@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

"""Widen ``contract_line.partner_order`` to 32 characters.

``contract.line`` inherits the fiscal document line mixin and therefore stores
the same field; widening the mixin does not resize the existing column.
"""


def migrate(cr, version):
    if not version:
        return
    cr.execute(
        """
        SELECT character_maximum_length
          FROM information_schema.columns
         WHERE table_name = 'contract_line'
           AND column_name = 'partner_order'
        """
    )
    row = cr.fetchone()
    if row and row[0] and row[0] < 32:
        cr.execute(
            "ALTER TABLE contract_line ALTER COLUMN partner_order TYPE varchar(32)"
        )
