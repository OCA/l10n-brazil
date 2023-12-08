# Copyright 2023 Engenere - Antônio S. Pereira Neto <neto@engenere.one>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openupgradelib import openupgrade

column_renames = {
    "account_invoice_account_financial_move_line_rel": [("account_invoice_id", None)]
}


@openupgrade.migrate()
def migrate(env, version):
    if openupgrade.column_exists(
        env.cr, "account_invoice_account_financial_move_line_rel", "account_invoice_id"
    ):
        openupgrade.logged_query(
            env.cr,
            """
            ALTER TABLE account_invoice_account_financial_move_line_rel
            DROP CONSTRAINT
            account_invoice_account_finan_account_invoice_id_account_mo_key
            """,
        )
        openupgrade.logged_query(
            env.cr,
            """
            ALTER TABLE account_invoice_account_financial_move_line_rel
            ALTER COLUMN account_invoice_id DROP NOT NULL
            """,
        )
        openupgrade.rename_columns(env.cr, column_renames)
        openupgrade.logged_query(
            env.cr,
            """
            ALTER TABLE account_invoice_account_financial_move_line_rel
            ADD COLUMN IF NOT EXISTS account_move_id int4
            """,
        )
