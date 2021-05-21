# Copyright (C) 2021 - TODAY Luis Felipe Mileo - KMEE
# License AGPL-3.0 or later (
# http://www.gnu.org/licenses/agpl.html).

from openupgradelib import openupgrade


def rg_migrate(env):
    openupgrade.logged_query(
        env.cr, """UPDATE res_partner set rg=inscr_est where is_company='f'""",
    )
    openupgrade.logged_query(
        env.cr, """UPDATE res_partner set inscr_est=null where is_company='f'""",
    )


@openupgrade.migrate()
def migrate(env, version):
    rg_migrate(env)
