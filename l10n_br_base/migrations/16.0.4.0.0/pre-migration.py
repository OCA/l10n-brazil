# Copyright (C) 2025 - TODAY Raphaël Valyi - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    if not openupgrade.column_exists(env.cr, "res_partner", "l10n_br_ie_code"):
        openupgrade.rename_columns(
            env.cr,
            {
                "res_partner": [
                    (
                        "inscr_est",
                        "l10n_br_ie_code",
                    )
                ]
            },
        )
