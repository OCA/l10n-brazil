# Copyright (C) 2024-Today - Akretion (<http://www.akretion.com>).
# @author Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openupgradelib import openupgrade


def update_cnab_config(env):
    """Atualiza a Configuração do CNAB"""
    env.cr.execute(
        """
        SELECT id FROM account_payment_mode WHERE payment_method_id IN
        (SELECT id FROM account_payment_method WHERE code IN ('240', '400', '500')
        AND payment_type = 'inbound');
        """
    )
    for row in env.cr.fetchall():
        payment_mode = env["account.payment.mode"].browse(row[0])
        cnab_config = env["l10n_br_cnab.config"].search(
            [
                ("bank_id", "=", payment_mode.fixed_journal_id.bank_id.id),
                ("payment_method_id", "=", payment_mode.payment_method_id.id),
            ]
        )
        cnab_config.cnab_processor = payment_mode.cnab_processor


@openupgrade.migrate()
def migrate(env, version):
    if not version:
        return
    update_cnab_config(env)
