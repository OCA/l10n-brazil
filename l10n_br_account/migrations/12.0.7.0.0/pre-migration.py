# Copyright (C) 2021 - Raphaêl Valyi - Akretion
# License AGPL-3.0 or later (
# http://www.gnu.org/licenses/agpl.html).

from openupgradelib import openupgrade

_column_renames = {
    # l10n_br_account/models/account_tax.py
    "l10n_br_fiscal_account_tax_rel": [
        ("l10n_br_fiscal_tax_id", "fiscal_tax_id"),
    ],
    # l10n_br_account/models/account_tax_template.py
    "l10n_br_fiscal_account_template_tax_rel": [
        ("l10n_br_fiscal_tax_id", "fiscal_tax_id"),
    ],
}


@openupgrade.migrate(use_env=True)
def migrate(env, version):
    openupgrade.rename_columns(env.cr, _column_renames)
    openupgrade.rename_tables(
        env.cr, [("l10n_br_fiscal_account_tax_rel", "fiscal_account_tax_rel")]
    )
    openupgrade.rename_tables(
        env.cr,
        [
            (
                "l10n_br_fiscal_account_template_tax_rel",
                "fiscal_account_template_tax_rel",
            )
        ],
    )
