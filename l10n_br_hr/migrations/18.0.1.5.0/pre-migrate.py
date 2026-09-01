# Copyright 2026 Escodoo
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    if openupgrade.column_exists(env.cr, "hr_employee", "talk_to"):
        openupgrade.logged_query(
            env.cr,
            """
            UPDATE hr_employee
               SET emergency_contact = talk_to
             WHERE talk_to IS NOT NULL
               AND talk_to != ''
               AND (emergency_contact IS NULL OR emergency_contact = '')
            """,
        )
        openupgrade.drop_columns(env.cr, [("hr_employee", "talk_to")])
