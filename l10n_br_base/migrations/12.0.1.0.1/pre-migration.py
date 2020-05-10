# Copyright (C) 2020 - TODAY Marcel Savegnago - Escodoo
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openupgradelib import openupgrade


@openupgrade.migrate(use_env=True)
def migrate(env, version):
    openupgrade.update_module_names(
        env.cr, [('l10n_br_simple', 'l10n_br_coa_simple'), ], merge_modules=True,)
