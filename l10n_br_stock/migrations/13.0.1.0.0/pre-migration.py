# Copyright 2023 KMEE - André Marcos Ferreira
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from openupgradelib import openupgrade

_column_renames = {
    "stock_picking": [("ie", "inscr_est")],
}

@openupgrade.migrate()
def migrate(env, version):
    if openupgrade.column_exists(env.cr, 'stock_picking', 'ie'):
         openupgrade.rename_columns(env.cr, _column_renames)
