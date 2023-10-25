# Copyright 2022 Engenere - Felipe Motter Pereira
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openupgradelib import openupgrade

from odoo import tools


@openupgrade.migrate()
def migrate(env, version):
    tools.convert_file(
        env.cr,
        "l10n_br_fiscal",
        "data/l10n_br_fiscal.ncm.csv",
        None,
        mode="init",
        noupdate=True,
        kind="init",
    )
