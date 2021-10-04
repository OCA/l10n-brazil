from openupgradelib import openupgrade


def street_migrate(env):
    openupgrade.logged_query(
        env.cr,
        """UPDATE res_partner set street_name=street WHERE street_name IS NULL""",
    )


@openupgrade.migrate()
def migrate(env, version):
    street_migrate(env)
