# Copyright (C) 2021 - TODAY Renato Lima - Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openupgradelib import openupgrade

_columns_rename = {
    'account_invoice': [
        ('incoterm', 'incoterm_id'),
    ],
}


@openupgrade.migrate(use_env=True)
def migrate(env, version):
    for table in _columns_rename.keys():
        for rename_column in _columns_rename[table]:
            if openupgrade.column_exists(env.cr, table, rename_column[0]):
                openupgrade.rename_columns(
                    env.cr, {table: [rename_column]})
