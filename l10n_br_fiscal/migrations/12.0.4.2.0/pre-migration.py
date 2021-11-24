# Copyright (C) 2021 - TODAY Renato Lima - Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openupgradelib import openupgrade

_columns_rename = {
    "l10n_br_fiscal_document": [
        ("amount_discount", "amount_discount_value"),
        ("amount_freight_value", "amount_freight"),
        ("amount_insurance_value", "amount_insurance"),
        ("amount_other_costs_value", "amount_other_value"),
    ],
    "l10n_br_fiscal_document_line": [("other_costs_value", "other_value")],
}


@openupgrade.migrate(use_env=True)
def migrate(env, version):
    for table in _columns_rename.keys():
        for rename_column in _columns_rename[table]:
            if openupgrade.column_exists(env.cr, table, rename_column[0]):
                openupgrade.rename_columns(env.cr, {table: [rename_column]})
