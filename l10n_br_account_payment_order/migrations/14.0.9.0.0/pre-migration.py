# Copyright (C) 2024-Today - Akretion (<http://www.akretion.com>).
# @author Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openupgradelib import openupgrade


def update_model_data(env):
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE ir_model_data SET model = 'l10n_br_cnab.code'
        WHERE model = 'l10n_br_cnab.mov.instruction.code'
        """,
    )
    # Codigo de Retorno
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE ir_model_data SET model = 'l10n_br_cnab.code'
        WHERE model = 'l10n_br_cnab.return.move.code'
        """,
    )
    # Codigo Carteira
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE ir_model_data SET model = 'l10n_br_cnab.code'
        WHERE model = 'l10n_br_cnab.boleto.wallet.code'
        """,
    )


@openupgrade.migrate(use_env=True)
def migrate(env, version):
    update_model_data(env)
