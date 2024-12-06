from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    columns_to_add = [
        ("sending_code_id", "INTEGER"),
        ("write_off_code_id", "INTEGER"),
        ("change_title_value_code_id", "INTEGER"),
        ("change_maturity_date_code_id", "INTEGER"),
        ("protest_title_code_id", "INTEGER"),
        ("suspend_protest_keep_wallet_code_id", "INTEGER"),
        ("suspend_protest_write_off_code_id", "INTEGER"),
        ("grant_rebate_code_id", "INTEGER"),
        ("cancel_rebate_code_id", "INTEGER"),
        ("grant_discount_code_id", "INTEGER"),
        ("cancel_discount_code_id", "INTEGER"),
        ("wallet_code_id", "INTEGER"),
    ]
    for column_name, data_type in columns_to_add:
        openupgrade.logged_query(
            env.cr,
            f"""
            ALTER TABLE account_payment_mode
            ADD COLUMN IF NOT EXISTS {column_name} {data_type};
            """,
        )
    openupgrade.logged_query(
        env.cr,
        """CREATE TABLE l10n_br_cnab_liq_return_move_code_rel
        (liq_return_move_code_id INTEGER, payment_mode_id INTEGER)""",
    )
