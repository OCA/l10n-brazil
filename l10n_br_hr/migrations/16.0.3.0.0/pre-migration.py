# Copyright (C) 2025 - TODAY Raphaël Valyi - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    if not openupgrade.column_exists(env.cr, "hr_employee", "l10n_br_rg_code"):
        openupgrade.rename_columns(
            env.cr,
            {
                "hr_employee": [
                    (
                        "rg",
                        "l10n_br_rg_code",
                    )
                ]
            },
        )
