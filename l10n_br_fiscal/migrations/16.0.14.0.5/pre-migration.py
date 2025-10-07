# Copyright (C) 2025  Renato Lima - Akretion <renato.lima@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    xmlids_renames = [
        (
            "l10n_br_fiscal.l10n_br_fiscal_operation_line_rule",
            "l10n_br_fiscal.l10n_br_fiscal_operation_rule",
        )
    ]
    openupgrade.rename_xmlids(env.cr, xmlids_renames)
