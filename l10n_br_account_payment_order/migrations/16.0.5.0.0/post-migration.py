# Copyright (C) 2024-Today - Akretion (<http://www.akretion.com>).
# @author Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openupgradelib import openupgrade


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
        # Instrução de Envio
        cnab_config.sending_code_id = payment_mode.sending_code_id

        # Solicitação de Baixa
        cnab_config.write_off_code_id = payment_mode.write_off_code_id

        # Alteração do Valor do título
        cnab_config.change_title_value_code_id = payment_mode.change_title_value_code_id

        # Alteração da Data de Vencimento
        cnab_config.change_maturity_date_code_id = (
            payment_mode.change_maturity_date_code_id
        )

        # Protesta o Título
        cnab_config.protest_title_code_id = payment_mode.protest_title_code_id

        # Suspende o Protesto e mantem a Carteira
        cnab_config.suspend_protest_keep_wallet_code_id = (
            payment_mode.suspend_protest_keep_wallet_code_id
        )

        # Suspende o Protesto e Baixa
        cnab_config.suspend_protest_write_off_code_id = (
            payment_mode.suspend_protest_write_off_code_id
        )

        # Concede Abatimento
        cnab_config.grant_rebate_code_id = payment_mode.grant_rebate_code_id

        # Cancela Abatimento
        cnab_config.cancel_rebate_code_id = payment_mode.cancel_rebate_code_id

        # Concede Desconto
        cnab_config.grant_discount_code_id = payment_mode.grant_discount_code_id

        # Cancela Disconto
        cnab_config.cancel_discount_code_id = payment_mode.cancel_discount_code_id

        # Codigo da Carteira
        cnab_config.wallet_code_id = payment_mode.wallet_code_id

        # Codigos de Return
        if payment_mode.cnab_liq_return_move_code_ids:
            liq_codes = env["l10n_br_cnab.code"]
            for code in payment_mode.liq_return_move_code_ids:
                liq_codes |= code

            cnab_config.liq_return_move_code_ids = liq_codes

        # Codigos ainda Char
        cnab_config.write(
            {
                "invoice_print": payment_mode.invoice_print,
                "instructions": payment_mode.instructions,
                "cnab_company_bank_code": payment_mode.cnab_company_bank_code,
                "convention_code": payment_mode.convention_code,
                "condition_issuing_paper": payment_mode.condition_issuing_paper,
                "communication_2": payment_mode.communication_2,
                "boleto_wallet": payment_mode.boleto_wallet,
                "boleto_modality": payment_mode.boleto_modality,
                "boleto_variation": payment_mode.boleto_variation,
                "boleto_accept": payment_mode.boleto_accept,
                "boleto_species": payment_mode.boleto_species,
                "boleto_protest_code": payment_mode.boleto_protest_code,
                "boleto_days_protest": payment_mode.boleto_days_protest,
                "generate_own_number": payment_mode.generate_own_number,
                "own_number_sequence_id": payment_mode.own_number_sequence_id.id,
                "cnab_sequence_id": payment_mode.cnab_sequence_id.id,
                "boleto_interest_code": payment_mode.boleto_interest_code,
                "boleto_interest_perc": payment_mode.boleto_interest_perc,
                "boleto_fee_code": payment_mode.boleto_fee_code,
                "boleto_fee_perc": payment_mode.boleto_fee_perc,
                "boleto_discount_perc": payment_mode.boleto_discount_perc,
                "boleto_byte_idt": payment_mode.boleto_byte_idt,
                "boleto_post": payment_mode.boleto_post,
            }
        )

        # Contas Contabeis
        if payment_mode.interest_fee_account_id:
            cnab_config.interest_fee_account_id = payment_mode.interest_fee_account_id
        if payment_mode.discount_account_id:
            cnab_config.discount_account_id = payment_mode.discount_account_id
        if payment_mode.rebate_account_id:
            cnab_config.rebate_account_id = payment_mode.rebate_account_id
        if payment_mode.tariff_charge_account_id:
            cnab_config.tariff_charge_account_id = payment_mode.tariff_charge_account_id
        if payment_mode.not_payment_account_id:
            cnab_config.not_payment_account_id = payment_mode.not_payment_account_id


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


@openupgrade.migrate()
def migrate(env, version):
    if not version:
        return
    update_payment_mode_inbound(env)
    update_payment_mode_outbound(env)
