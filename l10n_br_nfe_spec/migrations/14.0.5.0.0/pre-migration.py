# Copyright 2023 - TODAY, Raphaël Valyi <raphael.valyi@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.rename_models(
        env.cr, [("nfe.40.infevento", "nfe.40.tevento_infevento")]
    )
