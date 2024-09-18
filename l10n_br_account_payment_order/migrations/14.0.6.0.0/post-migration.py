# Copyright (C) 2024-Today - Akretion (<http://www.akretion.com>).
# @author Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openupgradelib import openupgrade


def unifying_cnab_codes(env):
    "Unifica os Codigos CNAB"

    # Codigo de Instrução do Movimento
    env.cr.execute(
        """
        SELECT id FROM l10n_br_cnab_mov_instruction_code
        """
    )
    for row in env.cr.fetchall():
        mov_instruction = env["l10n_br_cnab.mov.instruction.code"].browse(row[0])
        existing_code = env["l10n_br_cnab.code"].search(
            [("code", "=", mov_instruction.code)], limit=1
        )
        if existing_code:
            continue  # Skip
        env["l10n_br_cnab.code"].create(
            {
                "name": mov_instruction.name,
                "code": mov_instruction.code,
                "code_type": "instruction_move_code",
                "bank_ids": mov_instruction.bank_ids,
                "payment_method_ids": mov_instruction.payment_method_ids,
            }
        )

    # Codigo de Retorno do Movimento
    env.cr.execute(
        """
        SELECT id FROM l10n_br_cnab_return_move_code
        """
    )
    for row in env.cr.fetchall():
        return_code = env["l10n_br_cnab.return.move.code"].browse(row[0])
        existing_code = env["l10n_br_cnab.code"].search(
            [("code", "=", return_code.code)], limit=1
        )
        if existing_code:
            continue  # Skip
        env["l10n_br_cnab.code"].create(
            {
                "name": return_code.name,
                "code": return_code.code,
                "code_type": "return_move_code",
                "bank_ids": return_code.bank_ids,
                "payment_method_ids": return_code.payment_method_ids,
            }
        )

    # Codigo da Carteira
    env.cr.execute(
        """
        SELECT id FROM l10n_br_cnab_boleto_wallet_code
        """
    )
    for row in env.cr.fetchall():
        wallet_code = env["l10n_br_cnab.boleto.wallet.code"].browse(row[0])
        existing_code = env["l10n_br_cnab.code"].search(
            [("code", "=", wallet_code.code)], limit=1
        )
        if existing_code:
            continue  # Skip
        env["l10n_br_cnab.code"].create(
            {
                "name": wallet_code.name,
                "code": wallet_code.code,
                "code_type": "wallet_code",
                "bank_ids": wallet_code.bank_ids,
                "payment_method_ids": wallet_code.payment_method_ids,
            }
        )


def get_new_code(env, payment_mode, payment_mode_code, code_type):
    """Retorna o Codigo no novo objeto"""
    new_code = env["l10n_br_cnab.code"].search(
        [
            ("bank_ids", "in", payment_mode.bank_id.ids),
            ("payment_method_ids", "in", payment_mode.payment_method_id.ids),
            ("code", "=", payment_mode_code.code),
            ("code_type", "=", code_type),
        ]
    )
    return new_code


def update_payment_mode_inbound(env):
    """Atualiza o Modo de Pagamento"""
    env.cr.execute(
        """
        SELECT id FROM account_payment_mode WHERE payment_method_id IN
        (SELECT id FROM account_payment_method WHERE code IN ('240', '400', '500')
        AND payment_type = 'inbound');
        """
    )
    for row in env.cr.fetchall():
        payment_mode = env["account.payment.mode"].browse(row[0])

        # Atualizando os Codigos CNAB

        # Instrução de Envio
        sending_code = get_new_code(
            env,
            payment_mode,
            payment_mode.cnab_sending_code_id,
            "instruction_move_code",
        )
        payment_mode.sending_code_id = sending_code

        # Solicitação de Baixa
        write_off = get_new_code(
            env,
            payment_mode,
            payment_mode.cnab_write_off_code_id,
            "instruction_move_code",
        )
        payment_mode.write_off_code_id = write_off

        # Alteração do Valor do título
        change_title = get_new_code(
            env,
            payment_mode,
            payment_mode.cnab_code_change_title_value_id,
            "instruction_move_code",
        )
        payment_mode.change_title_value_code_id = change_title

        # Alteração da Data de Vencimento
        change_maturity = get_new_code(
            env,
            payment_mode,
            payment_mode.cnab_code_change_maturity_date_id,
            "instruction_move_code",
        )
        payment_mode.change_maturity_date_code_id = change_maturity

        # Protesta o Título
        protest_title = get_new_code(
            env,
            payment_mode,
            payment_mode.cnab_code_protest_title_id,
            "instruction_move_code",
        )
        payment_mode.protest_title_code_id = protest_title

        # Suspende o Protesto e mantem a Carteira
        suspend_protest_keep_wallet = get_new_code(
            env,
            payment_mode,
            payment_mode.cnab_code_suspend_protest_keep_wallet_id,
            "instruction_move_code",
        )
        payment_mode.suspend_protest_keep_wallet_code_id = suspend_protest_keep_wallet

        # Suspende o Protesto e Baixa
        suspend_protest_write_off = get_new_code(
            env,
            payment_mode,
            payment_mode.cnab_code_suspend_protest_write_off_id,
            "instruction_move_code",
        )
        payment_mode.suspend_protest_write_off_code_id = suspend_protest_write_off

        # Concede Abatimento
        grant_rebate = get_new_code(
            env,
            payment_mode,
            payment_mode.cnab_code_grant_rebate_id,
            "instruction_move_code",
        )
        payment_mode.grant_rebate_code_id = grant_rebate

        # Cancela Abatimento
        cancel_rebate = get_new_code(
            env,
            payment_mode,
            payment_mode.cnab_code_cancel_rebate_id,
            "instruction_move_code",
        )
        payment_mode.cancel_rebate_code_id = cancel_rebate

        # Concede Desconto
        grant_discount = get_new_code(
            env,
            payment_mode,
            payment_mode.cnab_code_grant_discount_id,
            "instruction_move_code",
        )
        payment_mode.grant_discount_code_id = grant_discount

        # Cancela Desconto
        cancel_discount = get_new_code(
            env,
            payment_mode,
            payment_mode.cnab_code_cancel_discount_id,
            "instruction_move_code",
        )
        payment_mode.cancel_discount_code_id = cancel_discount

        # Codigo da Carteira
        wallet_code = get_new_code(
            env,
            payment_mode,
            payment_mode.boleto_wallet_code_id,
            "wallet_code",
        )
        payment_mode.wallet_code_id = wallet_code

        # Codigos de Return
        if payment_mode.cnab_liq_return_move_code_ids:
            liq_codes = env["l10n_br_cnab.code"]
            for code in payment_mode.cnab_liq_return_move_code_ids:
                liq_code = get_new_code(env, payment_mode, code, "return_move_code")
                liq_codes |= liq_code

            payment_mode.liq_return_move_code_ids = liq_codes


def update_move_lines(env):
    """
    Atualiza as account move lines
    """
    env.cr.execute(
        """
        SELECT id FROM account_move_line WHERE payment_mode_id IN (
        SELECT id FROM account_payment_mode WHERE payment_method_id IN
        (SELECT id FROM account_payment_method WHERE code IN ('240', '400', '500')
        AND payment_type = 'inbound'));
        """
    )
    for row in env.cr.fetchall():
        line = env["account.move.line"].browse(row[0])
        new_code = get_new_code(
            env,
            line.payment_mode_id,
            line.mov_instruction_code_id,
            "instruction_move_code",
        )
        line.instruction_move_code_id = new_code


def update_payment_lines(env):
    """
    Atualiza as account payment lines
    """
    env.cr.execute(
        """
        SELECT id FROM account_payment_line WHERE mov_instruction_code_id IS NOT NULL;
        """
    )
    for row in env.cr.fetchall():
        line = env["account.payment.line"].browse(row[0])
        new_code = get_new_code(
            env,
            line.payment_mode_id,
            line.mov_instruction_code_id,
            "instruction_move_code",
        )
        line.instruction_move_code_id = new_code


@openupgrade.migrate()
def migrate(env, version):
    if not version:
        return
    unifying_cnab_codes(env)
    update_payment_mode_inbound(env)
    update_move_lines(env)
    update_payment_lines(env)
