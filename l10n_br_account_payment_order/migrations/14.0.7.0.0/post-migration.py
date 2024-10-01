# Copyright (C) 2024-Today - Akretion (<http://www.akretion.com>).
# @author Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openupgradelib import openupgrade


def update_payment_mode_inbound(env):
    """Atualiza o Modo de Pagamento"""
    env.cr.execute(
        """
        SELECT
            apm.id,
            apm.sending_code_id,
            apm.write_off_code_id,
            apm.change_title_value_code_id,
            apm.change_maturity_date_code_id,
            apm.protest_title_code_id,
            apm.suspend_protest_keep_wallet_code_id,
            apm.suspend_protest_write_off_code_id,
            apm.grant_rebate_code_id,
            apm.cancel_rebate_code_id,
            apm.grant_discount_code_id,
            apm.cancel_discount_code_id,
            apm.wallet_code_id,
            apm.invoice_print,
            apm.instructions,
            apm.cnab_company_bank_code,
            apm.convention_code,
            apm.condition_issuing_paper,
            apm.communication_2,
            apm.boleto_wallet,
            apm.boleto_modality,
            apm.boleto_variation,
            apm.boleto_accept,
            apm.boleto_species,
            apm.boleto_protest_code,
            apm.boleto_days_protest,
            apm.generate_own_number,
            apm.own_number_sequence_id,
            apm.cnab_sequence_id,
            apm.boleto_interest_code,
            apm.boleto_interest_perc,
            apm.boleto_fee_code,
            apm.boleto_fee_perc,
            apm.boleto_discount_perc,
            apm.boleto_byte_idt,
            apm.boleto_post,
            apm.interest_fee_account_id,
            apm.discount_account_id,
            apm.rebate_account_id,
            apm.tariff_charge_account_id,
            apm.not_payment_account_id
        FROM
            account_payment_mode AS apm
        WHERE
            apm.payment_method_id IN(
                SELECT acm.id FROM account_payment_method AS acm
                WHERE acm.code IN ('240', '400', '500')
                AND acm.payment_type = 'inbound'
            );
        """
    )
    for row in env.cr.fetchall():
        payment_mode = env["account.payment.mode"].browse(row[0])

        # Criação do CNAB Config
        cnab_config = env["l10n_br_cnab.config"].create(
            {
                "name": (
                    payment_mode.fixed_journal_id.bank_id.name
                    + " - CNAB "
                    + payment_mode.payment_method_id.code
                    + " ("
                    + payment_mode.payment_method_id.payment_type
                    + ")"
                ),
                "bank_id": payment_mode.fixed_journal_id.bank_id.id,
                "payment_method_id": payment_mode.payment_method_id.id,
            }
        )
        payment_mode.cnab_config_id = cnab_config

        # Atualizando os Codigos CNAB
        cnab_config.sending_code_id = row[1]
        cnab_config.write_off_code_id = row[2]
        cnab_config.change_title_value_code_id = row[3]
        cnab_config.change_maturity_date_code_id = row[4]
        cnab_config.protest_title_code_id = row[5]
        cnab_config.suspend_protest_keep_wallet_code_id = row[6]
        cnab_config.suspend_protest_write_off_code_id = row[7]
        cnab_config.grant_rebate_code_id = row[8]
        cnab_config.cancel_rebate_code_id = row[9]
        cnab_config.grant_discount_code_id = row[10]
        cnab_config.cancel_discount_code_id = row[11]
        cnab_config.wallet_code_id = row[12]

        # Codigos de Return
        env.cr.execute(
            f"""
        SELECT rel.payment_mode_id
        FROM l10n_br_cnab_liq_return_move_code_rel AS rel
        WHERE rel.liq_return_move_code_id = {row[0]}
        """
        )
        # as colunas na tabela acima estão invertidas.
        # os codigos CNAB estão no campo payment_mode_id
        liq_code_ids = [lrow[0] for lrow in env.cr.fetchall()]
        if liq_code_ids:
            cnab_config.liq_return_move_code_ids = [(6, 0, liq_code_ids)]

        # Codigos ainda Char
        cnab_config.write(
            {
                "invoice_print": row[13],
                "instructions": row[14],
                "cnab_company_bank_code": row[15],
                "convention_code": row[16],
                "condition_issuing_paper": row[17],
                "communication_2": row[18],
                "boleto_wallet": row[19],
                "boleto_modality": row[20],
                "boleto_variation": row[21],
                "boleto_accept": row[22],
                "boleto_species": row[23],
                "boleto_protest_code": row[24],
                "boleto_days_protest": row[25],
                "generate_own_number": row[26],
                "own_number_sequence_id": row[27],
                "cnab_sequence_id": row[28],
                "boleto_interest_code": row[29],
                "boleto_interest_perc": row[30],
                "boleto_fee_code": row[31],
                "boleto_fee_perc": row[32],
                "boleto_discount_perc": row[33],
                "boleto_byte_idt": row[34],
                "boleto_post": row[35],
            }
        )

        # Contas Contabeis
        account_fields = {
            36: "interest_fee_account_id",
            37: "discount_account_id",
            38: "rebate_account_id",
            39: "tariff_charge_account_id",
            40: "not_payment_account_id",
        }
        for index, field in account_fields.items():
            if row[index]:
                setattr(cnab_config, field, row[index])


def update_payment_mode_outbound(env):
    """Atualiza o Modo de Pagamento Outbound"""
    env.cr.execute(
        """
        SELECT id FROM account_payment_mode WHERE payment_method_id IN
        (SELECT id FROM account_payment_method WHERE code IN ('240', '400', '500')
        AND payment_type = 'outbound');
        """
    )
    for row in env.cr.fetchall():
        payment_mode = env["account.payment.mode"].browse(row[0])
        # Criação do CNAB Config
        cnab_config = env["l10n_br_cnab.config"].create(
            {
                "name": (
                    payment_mode.fixed_journal_id.bank_id.name
                    + " - CNAB "
                    + payment_mode.payment_method_id.code
                    + " ("
                    + payment_mode.payment_method_id.payment_type
                    + ")"
                ),
                "bank_id": payment_mode.fixed_journal_id.bank_id.id,
                "payment_method_id": payment_mode.payment_method_id.id,
            }
        )
        payment_mode.cnab_config_id = cnab_config

        # Codigos ainda Char
        cnab_config.write(
            {
                "doc_finality_code": payment_mode.doc_finality_code,
                "ted_finality_code": payment_mode.ted_finality_code,
                "complementary_finality_code": payment_mode.complementary_finality_code,
                "favored_warning": payment_mode.favored_warning,
            }
        )


def clean_demo_cnab_config(env):
    """
    Função para limpar as configurações CNAB na migração de testes
    utilizando os dados de demonstracão.
    """
    env.cr.execute(
        "SELECT demo FROM ir_module_module WHERE name='l10n_br_account_payment_order';"
    )
    is_demo = env.cr.fetchone()[0]
    if is_demo:
        env["l10n_br_cnab.config"].search([]).unlink()


@openupgrade.migrate()
def migrate(env, version):
    if not version:
        return
    clean_demo_cnab_config(env)
    update_payment_mode_inbound(env)
    update_payment_mode_outbound(env)
