# Copyright 2023 Engenere - Antônio S. P. Neto
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE account_move am
        SET instructions = ai.instructions
        FROM account_invoice ai
        WHERE ai.id = am.old_invoice_id AND ai.instructions IS NOT NULL
        """,
    )
