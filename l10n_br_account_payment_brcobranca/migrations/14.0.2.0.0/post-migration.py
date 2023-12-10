from openupgradelib import openupgrade


def populate_cnab_processor(env):
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE account_payment_mode
        AS apm
        SET cnab_processor='brcobranca'
        WHERE apm.payment_method_code IN ('240', '400', '500')
        AND apm.cnab_processor IS NULL
        """,
    )


@openupgrade.migrate()
def migrate(env, version):
    populate_cnab_processor(env)
