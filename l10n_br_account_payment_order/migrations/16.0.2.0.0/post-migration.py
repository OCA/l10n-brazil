# Copyright (C) 2024-Today - Akretion (<http://www.akretion.com>).
# @author Magno Costa <magno.costa@akretion.com.br>
# Copyright (C) 2024-Today - Engenere (<https://engenere.one>).
# @author Antônio S. Pereira Neto <neto@engenere.one>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openupgradelib import openupgrade

from odoo import Command


def unifying_cnab_codes(env):
    # Codigo de Instrução do Movimento
    env.cr.execute(
        """
    SELECT lcmic.id, lcmic.name, lcmic.code, lcmic.bank_id, lcmic.payment_method_id
    FROM l10n_br_cnab_mov_instruction_code AS lcmic
    WHERE NOT EXISTS (
        SELECT 1 FROM l10n_br_cnab_code AS lcc
        WHERE lcc.code = lcmic.code
        AND lcc.code_type = 'instruction_move_code'
        AND lcc.bank_id = lcmic.bank_id
        AND lcc.payment_method_id = lcmic.payment_method_id
    );
    """
    )
    for row in env.cr.fetchall():
        # Inserir na tabela l10n_br_cnab_code
        env.cr.execute(
            """
            INSERT INTO l10n_br_cnab_code (
                name, code, bank_id, payment_method_id,  code_type
            )
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
            """,
            (row[1], row[2], row[3], row[4], "instruction_move_code"),
        )
        new_id = env.cr.fetchone()[0]

        # Relação com bancos
        env.cr.execute(
            f"""
            SELECT l10n_br_cnab_mov_instruction_code_id
            FROM l10n_br_cnab_mov_instruction_code_bank_rel
            WHERE bank_id = {row[0]}
        """
        )
        bank_ids = [bank_id[0] for bank_id in env.cr.fetchall()]
        if bank_ids:
            bank_values = [(bank_id, new_id) for bank_id in bank_ids]
            env.cr.executemany(
                """
                INSERT INTO l10n_br_cnab_code_bank_rel (l10n_br_cnab_code_id, bank_id)
                VALUES (%s, %s)
                """,
                bank_values,
            )

        # Relação com métodos de pagamento
        env.cr.execute(
            f"""
            SELECT l10n_br_cnab_mov_instruction_code_id
            FROM l10n_br_cnab_mov_instruction_code_payment_method_rel
            WHERE payment_method_id = {row[0]}
        """
        )
        payment_method_ids = [
            payment_method_id[0] for payment_method_id in env.cr.fetchall()
        ]
        if payment_method_ids:
            pm_values = [(pm_id, new_id) for pm_id in payment_method_ids]
            env.cr.executemany(
                """
                INSERT INTO l10n_br_cnab_code_payment_method_rel (
                l10n_br_cnab_code_id, payment_method_id)
                VALUES (%s, %s)
                """,
                pm_values,
            )

    # Codigo de Retorno do Movimento
    env.cr.execute(
        """
    SELECT lcmic.id, lcmic.name, lcmic.code
    FROM l10n_br_cnab_return_move_code AS lcmic
    WHERE NOT EXISTS (
        SELECT 1 FROM l10n_br_cnab_code AS lcc
        WHERE lcc.code = lcmic.code
        AND lcc.code_type = 'return_move_code'
        AND lcc.bank_id = lcmic.bank_id
        AND lcc.payment_method_id = lcmic.payment_method_id
    );
    """
    )
    for row in env.cr.fetchall():
        # Relação bank_ids x return_move_code
        bank_id_colunm = "l10n_br_cnab_return_move_code_id"
        return_move_code_id_colunm = "bank_id"
        env.cr.execute(
            f"""
            SELECT {bank_id_colunm}
            FROM l10n_br_cnab_return_move_code_bank_rel
            WHERE {return_move_code_id_colunm} = {row[0]}
        """
        )
        bank_ids = [bank_id[0] for bank_id in env.cr.fetchall()]

        # Relação payment_method_ids x return_move_code
        payment_method_id_colunm = (
            "l10n_br_cnab_mov_instruction_code_id"
        )  # nome tava errado
        return_move_code_id_colunm = "payment_method_id"
        env.cr.execute(
            f"""
            SELECT {payment_method_id_colunm}
            FROM l10n_br_cnab_return_move_code_payment_method_rel
            WHERE {return_move_code_id_colunm} = {row[0]}
        """
        )
        payment_method_ids = [
            payment_method_id[0] for payment_method_id in env.cr.fetchall()
        ]
        env["l10n_br_cnab.code"].create(
            {
                "name": row[1],
                "code": row[2],
                "code_type": "return_move_code",
                "bank_ids": [Command.set(bank_ids)],
                "payment_method_ids": [Command.set(payment_method_ids)],
            }
        )

    # Codigo da Carteira
    env.cr.execute(
        """
    SELECT lcmic.id, lcmic.name, lcmic.code, lcmic.bank_id, lcmic.payment_method_id
    FROM l10n_br_cnab_boleto_wallet_code AS lcmic
    WHERE NOT EXISTS (
        SELECT 1 FROM l10n_br_cnab_code AS lcc
        WHERE lcc.code = lcmic.code
        AND lcc.code_type = 'wallet_code'
        AND lcc.bank_id = lcmic.bank_id
        AND lcc.payment_method_id = lcmic.payment_method_id
    );
    """
    )
    for row in env.cr.fetchall():
        # Relação bank_ids x boleto_wallet_code
        bank_id_colunm = "l10n_br_cnab_boleto_wallet_code_id"
        boleto_wallet_id_colunm = "bank_id"
        env.cr.execute(
            f"""
            SELECT {bank_id_colunm}
            FROM l10n_br_cnab_boleto_wallet_code_bank_rel
            WHERE {boleto_wallet_id_colunm} = {row[0]}
        """
        )
        bank_ids = [bank_id[0] for bank_id in env.cr.fetchall()]

        # Relação payment_method_ids x boleto_wallet_code
        payment_method_id_colunm = "l10n_br_cnab_boleto_wallet_code_id"
        boleto_wallet_id_colunm = "payment_method_id"
        env.cr.execute(
            f"""
            SELECT {payment_method_id_colunm}
            FROM l10n_br_cnab_boleto_wallet_code_payment_method_rel
            WHERE {boleto_wallet_id_colunm} = {row[0]}
        """
        )
        payment_method_ids = [
            payment_method_id[0] for payment_method_id in env.cr.fetchall()
        ]
        env["l10n_br_cnab.code"].create(
            {
                "name": row[1],
                "code": row[2],
                "code_type": "wallet_code",
                "bank_ids": [Command.set(bank_ids)],
                "payment_method_ids": [Command.set(payment_method_ids)],
            }
        )


def update_payment_mode(env):
    fields = [
        (
            "cnab_sending_code_id",
            "sending_code_id",
            "instruction_move_code",
            "l10n_br_cnab_mov_instruction_code",
        ),
        (
            "cnab_write_off_code_id",
            "write_off_code_id",
            "instruction_move_code",
            "l10n_br_cnab_mov_instruction_code",
        ),
        (
            "cnab_code_change_title_value_id",
            "change_title_value_code_id",
            "instruction_move_code",
            "l10n_br_cnab_mov_instruction_code",
        ),
        (
            "cnab_code_change_maturity_date_id",
            "change_maturity_date_code_id",
            "instruction_move_code",
            "l10n_br_cnab_mov_instruction_code",
        ),
        (
            "cnab_code_protest_title_id",
            "protest_title_code_id",
            "instruction_move_code",
            "l10n_br_cnab_mov_instruction_code",
        ),
        (
            "cnab_code_suspend_protest_keep_wallet_id",
            "suspend_protest_keep_wallet_code_id",
            "instruction_move_code",
            "l10n_br_cnab_mov_instruction_code",
        ),
        (
            "cnab_code_suspend_protest_write_off_id",
            "suspend_protest_write_off_code_id",
            "instruction_move_code",
            "l10n_br_cnab_mov_instruction_code",
        ),
        (
            "cnab_code_grant_rebate_id",
            "grant_rebate_code_id",
            "instruction_move_code",
            "l10n_br_cnab_mov_instruction_code",
        ),
        (
            "cnab_code_cancel_rebate_id",
            "cancel_rebate_code_id",
            "instruction_move_code",
            "l10n_br_cnab_mov_instruction_code",
        ),
        (
            "cnab_code_grant_discount_id",
            "grant_discount_code_id",
            "instruction_move_code",
            "l10n_br_cnab_mov_instruction_code",
        ),
        (
            "cnab_code_cancel_discount_id",
            "cancel_discount_code_id",
            "instruction_move_code",
            "l10n_br_cnab_mov_instruction_code",
        ),
        (
            "boleto_wallet_code_id",
            "wallet_code_id",
            "wallet_code",
            "l10n_br_cnab_boleto_wallet_code",
        ),
    ]
    for old_field, new_field, code_type, old_table in fields:
        sql = f"""
            UPDATE account_payment_mode AS apm
            SET {new_field} = lcc.id
            FROM {old_table} AS ot
            JOIN l10n_br_cnab_code AS lcc
                ON lcc.code = ot.code
                AND lcc.code_type = '{code_type}'
                AND lcc.bank_id = ot.bank_id
                AND lcc.payment_method_id = ot.payment_method_id
            WHERE apm.{old_field} = ot.id;
        """
        openupgrade.logged_query(env.cr, sql)


def get_cnab_return_code(env, payment_mode_id):
    env.cr.execute(
        """
        SELECT *
        FROM l10n_br_cnab_return_liquidity_move_code_rel
        """
    )
    liq_codes = env["l10n_br_cnab.code"]
    for row in env.cr.fetchall():
        if row[0] != payment_mode_id:
            continue
        env.cr.execute(
            f"""
            SELECT name, code, bank_id, payment_method_id
            FROM l10n_br_cnab_return_move_code
            WHERE id = {row[1]}
            """
        )
        for old_code in env.cr.fetchall():
            new_code = env["l10n_br_cnab.code"].search(
                [
                    ("name", "=", old_code[0]),
                    ("code", "=", old_code[1]),
                    ("bank_id", "=", old_code[2]),
                    ("payment_method_id", "=", old_code[3]),
                ]
            )

            if new_code:
                liq_codes |= new_code

    return liq_codes


def get_wallet_code(env, payment_mode_id):
    env.cr.execute(
        f"""
        SELECT boleto_wallet_code_id
        FROM account_payment_mode
        WHERE id = {payment_mode_id}
        """
    )
    wallet_code = env["l10n_br_cnab.code"]
    for row in env.cr.fetchall():
        if row[0] is None:
            continue

        env.cr.execute(
            f"""
            SELECT name, code, bank_id, payment_method_id
            FROM l10n_br_cnab_boleto_wallet_code
            WHERE id = {row[0]}
            """
        )
        for old_code in env.cr.fetchall():
            new_code = env["l10n_br_cnab.code"].search(
                [
                    ("name", "=", old_code[0]),
                    ("code", "=", old_code[1]),
                    ("bank_id", "=", old_code[2]),
                    ("payment_method_id", "=", old_code[3]),
                    ("code_type", "=", "wallet_code"),
                ]
            )
            if new_code:
                wallet_code = new_code

    return wallet_code


def uptade_payment_mode_return_code(env):
    env.cr.execute(
        """
        SELECT id FROM account_payment_mode WHERE payment_method_id IN
        (SELECT id FROM account_payment_method WHERE code IN ('240', '400', '500')
        AND payment_type = 'inbound');
        """
    )
    for row in env.cr.fetchall():
        payment_mode = env["account.payment.mode"].browse(row[0])
        liq_codes = get_cnab_return_code(env, row[0])
        if liq_codes:
            payment_mode.liq_return_move_code_ids = liq_codes

        wallet_code = get_wallet_code(env, row[0])
        if wallet_code:
            sql = f"""
               UPDATE account_payment_mode
               SET wallet_code_id = {wallet_code.id}
               WHERE id = {payment_mode.id}
            """
            openupgrade.logged_query(env.cr, sql)


def update_move_lines(env):
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE account_move_line AS aml
        SET instruction_move_code_id = lcc.id
        FROM l10n_br_cnab_mov_instruction_code AS lcmic
        JOIN l10n_br_cnab_code AS lcc
            ON lcc.code = lcmic.code
            AND lcc.code_type = 'instruction_move_code'
            AND lcc.bank_id = lcmic.bank_id
            AND lcc.payment_method_id = lcmic.payment_method_id
        WHERE aml.mov_instruction_code_id = lcmic.id
        """,
    )


def update_payment_lines(env):
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE account_payment_line AS apl
        SET instruction_move_code_id = lcc.id
        FROM l10n_br_cnab_mov_instruction_code AS lcmic
        JOIN l10n_br_cnab_code AS lcc
            ON lcc.code = lcmic.code
            AND lcc.code_type = 'instruction_move_code'
            AND lcc.bank_id = lcmic.bank_id
            AND lcc.payment_method_id = lcmic.payment_method_id
        WHERE apl.mov_instruction_code_id = lcmic.id;
        """,
    )


@openupgrade.migrate()
def migrate(env, version):
    if not version:
        return

    if "sending_code_id" in env["account.payment.mode"]._fields:
        # Caso o campo ainda exista,
        # checamos se já há registros (indicando migração prévia).
        payment_mode_migrated = env["account.payment.mode"].search(
            [("sending_code_id", "!=", False)],
            limit=1,
        )
    else:
        # Caso o campo não exista,
        # assumimos que a migração já foi suficientemente avançada.
        payment_mode_migrated = True

    if payment_mode_migrated:
        return

    unifying_cnab_codes(env)
    update_payment_mode(env)
    uptade_payment_mode_return_code(env)
    update_move_lines(env)
    update_payment_lines(env)
