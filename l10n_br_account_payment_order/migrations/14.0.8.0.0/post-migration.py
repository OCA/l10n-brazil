# Copyright (C) 2024-Today - Akretion (<http://www.akretion.com>).
# @author Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openupgradelib import openupgrade


def update_payment_mode_discount_code(env):
    """Atualiza o Código de Desconto"""
    env.cr.execute(
        """
        SELECT id FROM account_payment_mode WHERE payment_method_id IN
        (SELECT id FROM account_payment_method WHERE code IN ('240', '400', '500')
        AND payment_type = 'inbound');
        """
    )
    for row in env.cr.fetchall():
        payment_mode = env["account.payment.mode"].browse(row[0])
        cnab_config = payment_mode.cnab_config_id

        discount_value = "0"
        if cnab_config.boleto_discount_perc > 0.0:
            discount_value = "1"

        discount_code = env["l10n_br_cnab.code"].search(
            [
                ("bank_ids", "in", payment_mode.bank_id.ids),
                ("payment_method_ids", "in", payment_mode.payment_method_id.ids),
                ("code_type", "=", "discount_code"),
                ("code", "=", discount_value),
            ]
        )
        if discount_code:
            cnab_config.boleto_discount_code_id = discount_code


@openupgrade.migrate()
def migrate(env, version):
    if not version:
        return
    update_payment_mode_discount_code(env)
