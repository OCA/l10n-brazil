# Copyright (C) 2025-Today - Akretion (<http://www.akretion.com>).
# @author Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests.common import Form

# TODO: Seria possível fazer isso de forma abstrata?
#  Para não precisar de multiplos métodos


def create_with_form_ir_sequence(env, values):
    # if model == "ir.sequence":
    with Form(env["ir.sequence"]) as seq:
        seq.name = values.get("name")
        seq.code = values.get("code")
        seq.number_next_actual = values.get("number_next_actual")
        seq.number_increment = values.get("number_increment")
        seq.padding = values.get("padding")
    return seq.save()


def create_with_form_account_account(env, values):
    with Form(env["account.account"]) as account:
        account.name = values.get("name")
        account.code = values.get("code")
        account.account_type = values.get("account_type")
    return account.save()


def create_with_form_res_partner_bank(env, values):
    with Form(
        env["res.partner.bank"].with_context(
            default_company_id=values.get("company_id")
        )
    ) as partner_bank:
        partner_bank.acc_number = values.get("acc_number")
        partner_bank.acc_number_dig = values.get("acc_number_dig")
        partner_bank.bra_number = values.get("bra_number")
        partner_bank.bra_number_dig = values.get("bra_number_dig")
        partner_bank.bank_id = values.get("bank_id")
        partner_bank.partner_id = values.get("partner_id")
    return partner_bank.save()


def create_with_form_account_journal(env, values, line_values=False):
    with Form(env["account.journal"]) as journal:
        journal.name = values.get("name")
        journal.code = values.get("code")
        journal.type = values.get("type")
        if values.get("type") == "bank":
            journal.bank_account_id = values.get("bank_account_id")
        else:
            journal.default_account_id = values.get("default_account_id")
        for line_dict in line_values:
            with journal.inbound_payment_method_line_ids.new() as line:
                line.name = line_dict.get("name")
                line.payment_method_id = line_dict.get("payment_method_id")
    return journal.save()


def create_with_form_l10n_br_cnab_config(env, values):
    with Form(
        env["l10n_br_cnab.config"],
        "l10n_br_account_payment_order.l10n_br_cnab_config_form_view",
    ) as cnab_config:
        cnab_config.name = values.get("name")
        cnab_config.bank_id = values.get("bank_id")
        cnab_config.payment_method_id = values.get("payment_method_id")
        if values.get("cnab_processor"):
            cnab_config.cnab_processor = values.get("cnab_processor")
        cnab_config.cnab_company_bank_code = values.get("cnab_company_bank_code")
        if values.get("convention_code"):
            cnab_config.convention_code = values.get("convention_code")
        cnab_config.boleto_wallet = values.get("boleto_wallet")
        cnab_config.boleto_modality = values.get("boleto_modality")
        cnab_config.boleto_variation = values.get("boleto_variation")
        cnab_config.boleto_accept = values.get("boleto_accept")
        if values.get("boleto_protest_code_id"):
            cnab_config.boleto_protest_code_id = values.get("boleto_protest_code_id")
        if values.get("boleto_discount_perc"):
            cnab_config.boleto_discount_perc = values.get("boleto_discount_perc")
        cnab_config.boleto_days_protest = values.get("boleto_days_protest")
        cnab_config.boleto_interest_code = values.get("boleto_interest_code")
        cnab_config.boleto_interest_perc = values.get("boleto_interest_perc")
        cnab_config.cnab_sequence_id = values.get("cnab_sequence_id")
        cnab_config.own_number_sequence_id = values.get("own_number_sequence_id")
        cnab_config.generate_own_number = values.get("generate_own_number")
        if values.get("wallet_code_id"):
            cnab_config.wallet_code_id = values.get("wallet_code_id")
        if values.get("write_off_devolution_code_id"):
            cnab_config.write_off_devolution_code_id = values.get(
                "write_off_devolution_code_id"
            )
            cnab_config.write_off_devolution_number_of_days = values.get(
                "write_off_devolution_number_of_days"
            )

        cnab_config.tariff_charge_account_id = values.get("tariff_charge_account_id")
        cnab_config.interest_fee_account_id = values.get("interest_fee_account_id")
        cnab_config.discount_account_id = values.get("discount_account_id")
        cnab_config.rebate_account_id = values.get("rebate_account_id")
        cnab_config.not_payment_account_id = values.get("not_payment_account_id")
        cnab_config.sending_code_id = values.get("sending_code_id")
        cnab_config.write_off_code_id = values.get("write_off_code_id")

        # TODO: Verificar a possibilidade de incluir um campo to tipo many2many
        #  com o Form, tentei [(6,0,[178, 203])], l10n_br_cnab.code(178, 179),
        #  [178, 203] porém retorna o erro:
        #
        #  odoo/tests/common.py", line 2350, in __setattr__
        #  assert descr['type'] not in ('many2many', 'one2many'), \
        #  AssertionError: Can't set an o2m or m2m field, manipulate the
        #  corresponding proxies
        # if values.get("liq_return_move_code_ids"):
        #    cnab_config.liq_return_move_code_ids = values.get(
        #         "liq_return_move_code_ids"
        #     )

        if values.get("change_title_value_code_id"):
            # UNICRED 400 não tem
            cnab_config.change_title_value_code_id = values.get(
                "change_title_value_code_id"
            )
        if values.get("change_maturity_date_code_id"):
            cnab_config.change_maturity_date_code_id = values.get(
                "change_maturity_date_code_id"
            )
        if values.get("protest_title_code_id"):
            cnab_config.protest_title_code_id = values.get("protest_title_code_id")
        if values.get("suspend_protest_keep_wallet_code_id"):
            # Itau 400 não tem
            cnab_config.suspend_protest_keep_wallet_code_id = values.get(
                "suspend_protest_keep_wallet_code_id"
            )
        if values.get("grant_discount_code_id"):
            # Itau 400 não tem
            cnab_config.grant_rebate_code_id = values.get("grant_rebate_code_id")
            cnab_config.cancel_rebate_code_id = values.get("cancel_rebate_code_id")
        if values.get("grant_discount_code_id"):
            # UNICRED 400 não tem
            cnab_config.grant_discount_code_id = values.get("grant_discount_code_id")
            cnab_config.cancel_discount_code_id = values.get("cancel_discount_code_id")
        if values.get("boleto_byte_idt"):
            cnab_config.boleto_byte_idt = values.get("boleto_byte_idt")
            cnab_config.boleto_post = values.get("boleto_post")

    return cnab_config.save()


def create_with_form_account_payment_mode(env, values, line_values=False):
    with Form(env["account.payment.mode"]) as pay_mode:
        pay_mode.name = values.get("name")
        pay_mode.bank_account_link = values.get("bank_account_link")
        pay_mode.fixed_journal_id = values.get("fixed_journal_id")
        pay_mode.payment_order_ok = values.get("payment_order_ok")
        pay_mode.auto_create_payment_order = values.get("auto_create_payment_order")
        pay_mode.payment_method_id = values.get("payment_method_id")
        pay_mode.group_lines = values.get("group_lines")
        if values.get("cnab_config_id"):
            pay_mode.cnab_config_id = values.get("cnab_config_id")
    return pay_mode.save()


def create_with_form_account_move(env, values, line_values=False):
    with Form(
        env["account.move"].with_context(default_move_type="out_invoice")
    ) as invoice:
        invoice.partner_id = values.get("partner_id")
        invoice.invoice_payment_term_id = values.get("invoice_payment_term_id")
        if values.get("payment_mode_id"):
            invoice.payment_mode_id = values.get("payment_mode_id")

        with invoice.invoice_line_ids.new() as line:
            line.product_id = line_values.get("product_id")
            line.price_unit = line_values.get("price_unit")
            line.quantity = line_values.get("quantity")
            line.account_id = line_values.get("account_id")

    return invoice.save()
