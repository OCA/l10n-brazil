# Copyright (C) 2020 - TODAY Renato Lima - Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openupgradelib import openupgrade

_columns_rename = {
    'l10n_br_fiscal_document': [
        ('additional_data', 'fiscal_additional_data')],
}


@openupgrade.migrate(use_env=True)
def migrate(env, version):
    openupgrade.rename_columns(env.cr, _columns_rename)
