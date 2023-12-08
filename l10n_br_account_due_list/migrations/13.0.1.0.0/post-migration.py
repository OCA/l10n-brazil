# Copyright 2023 Engenere - Antônio S. P. Neto
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE account_invoice_account_financial_move_line_rel rel_table
        SET account_move_id = am.id
        FROM account_move am
        WHERE rel_table.{old_invoice_id} = am.old_invoice_id
        """.format(
            old_invoice_id=openupgrade.get_legacy_name("account_invoice_id")
        ),
    )
