# Copyright (C) 2020 - TODAY Renato Lima - Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openupgradelib import openupgrade

_column_renames = {
    "l10n_br_fiscal_document": [("operation_type", "fiscal_operation_type")],
    "l10n_br_fiscal_operation": [("operation_type", "fiscal_operation_type")],
    "l10n_br_fiscal_operation_line": [("operation_type", "fiscal_operation_type")],
}


@openupgrade.migrate(use_env=True)
def migrate(env, version):
    if openupgrade.table_exists(env.cr, "l10n_br_fiscal_document"):
        openupgrade.rename_columns(env.cr, _column_renames)
