# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


def pre_init_hook(cr):
    """Create the stored computed columns empty: no journal item has an
    instrument yet, so nothing has to be computed on install."""
    cr.execute(
        """
        ALTER TABLE account_move_line
        ADD COLUMN IF NOT EXISTS payment_digitable_line varchar,
        ADD COLUMN IF NOT EXISTS payment_barcode_type varchar,
        ADD COLUMN IF NOT EXISTS payment_pix_check varchar
        """
    )
