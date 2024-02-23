# Copyright (C) 2024-Today - Akretion (<http://www.akretion.com>).
# @author Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openupgradelib import openupgrade

_column_renames = {
    "account_payment_mode": [
        ("code_convetion", "cnab_company_bank_code"),
        ("code_convenio_lider", "convention_code"),
    ],
}


@openupgrade.migrate(use_env=True)
def migrate(env, version):

    # Apagando o objeto bank.payment.line
    openupgrade.logged_query(
        env.cr,
        """
        DELETE FROM ir_model_fields WHERE model = 'bank.payment.line'
        """,
    )
    openupgrade.logged_query(
        env.cr,
        """
        DELETE FROM ir_model WHERE model = 'bank.payment.line'
        """,
    )
    openupgrade.rename_columns(env.cr, _column_renames)
