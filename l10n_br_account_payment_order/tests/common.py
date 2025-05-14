# Copyright (C) 2021-Today - KMEE (<http://kmee.com.br>).
# @author Luis Felipe Mileo <mileo@kmee.com.br>
# Copyright (C) 2024-Today - Akretion (<http://www.akretion.com>).
# @author Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import date

from dateutil.relativedelta import relativedelta

from odoo.exceptions import UserError
from odoo.fields import Date
from odoo.tests import Form, tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon

from .tools import (
    create_with_form_account_account,
    create_with_form_account_journal,
    create_with_form_account_move,
    create_with_form_account_payment_mode,
    create_with_form_ir_sequence,
    create_with_form_l10n_br_cnab_config,
    create_with_form_res_partner_bank,
)


@tagged("post_install", "-at_install")
class CNABTestCommon(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))

        companies = cls.env["res.company"].search([])
        for company in companies:
            cls.env.user.company_ids += company

        # Contas Contabéis
        # Conta Contabil - Linha da Fatura
        cls.income_products_account = create_with_form_account_account(
            cls.env,
            {
                "name": "Receita da Venda no Mercado Interno de Produtos de"
                "Fabricação Própria - AVOID_TRAVIS_ERROR",
                "code": "3010101010200",
                "account_type": "income",
            },
        )
        # Conta Contabil de Tarifa Bancaria para Modo de Pagamento
        cls.tariff_charge_account = create_with_form_account_account(
            cls.env,
            {
                "name": "Outras Despesas Financeiras - AVOID_TRAVIS_ERROR",
                "code": "32302",
                "account_type": "expense",
            },
        )
        # Conta Contabil de Juros/Multa para Modo de Pagamento
        cls.interest_fee_account = create_with_form_account_account(
            cls.env,
            {
                "name": "Juros Ativos - AVOID_TRAVIS_ERROR",
                "code": "31202",
                "account_type": "income",
            },
        )
        # Conta Contabil de Desconto para Modo de Pagamento
        cls.discount_account = create_with_form_account_account(
            cls.env,
            {
                "name": "Despesas com Vendas - AVOID_TRAVIS_ERROR",
                "code": "32202",
                "account_type": "expense",
            },
        )
        # Conta Contabil de Abatimento para Modo de Pagamento
        cls.rebate_account = create_with_form_account_account(
            cls.env,
            {
                "name": "Outras Despesas Gerais - AVOID_TRAVIS_ERROR",
                "code": "32203",
                "account_type": "expense",
            },
        )
        # Conta Contabil de Não Pagamento/Inadimplencia para Modo de Pagamento
        cls.not_payment_account = create_with_form_account_account(
            cls.env,
            {
                "name": "Não Pagamento/Inadimplencia - AVOID_TRAVIS_ERROR",
                "code": "32333",
                "account_type": "expense",
            },
        )

        # Método de Pagamento
        cls.pay_method_type_240 = cls.env.ref(
            "l10n_br_account_payment_order.payment_mode_type_cnab240"
        )

        cls.pay_method_type_400 = cls.env.ref(
            "l10n_br_account_payment_order.payment_mode_type_cnab400"
        )

        cls.pay_method_type_500 = cls.env.ref(
            "l10n_br_account_payment_order.payment_mode_type_cnab500"
        )

        cls.pay_method_manual_test = cls.env.ref(
            "account.account_payment_method_manual_in"
        )

        # Conta Bancaria
        cls.bank_account_cef = create_with_form_res_partner_bank(
            cls.env,
            {
                "acc_number": "515",
                "acc_number_dig": "3",
                "bra_number": "1565",
                "bra_number_dig": "1",
                "bank_id": cls.env.ref("l10n_br_base.res_bank_104"),
                "partner_id": cls.env.company.partner_id,
            },
        )

        cls.bank_account_itau = create_with_form_res_partner_bank(
            cls.env,
            {
                "acc_number": "15019",
                "acc_number_dig": "0",
                "bra_number": "8517",
                "bra_number_dig": "0",
                "bank_id": cls.env.ref("l10n_br_base.res_bank_341"),
                "partner_id": cls.env.company.partner_id,
            },
        )

        # Sequencias
        cls.common_sequence_values = {
            "number_next_actual": "1",
            "number_increment": "1",
        }
        # Arquivo CNAB
        cls.cnab_seq_cef = create_with_form_ir_sequence(
            cls.env,
            cls.common_sequence_values
            | {
                "name": "Sequencia Arquivo CNAB - CEF 240",
                "code": "Sequencia Arquivo CNAB - CEF 240",
            },
        )

        # Nosso Número
        cls.own_number_seq_cef = create_with_form_ir_sequence(
            cls.env,
            cls.common_sequence_values
            | {
                "name": "Nosso número CEF",
                "code": "nosso.numero",
            },
        )

        cls.cnab_seq_itau_400 = create_with_form_ir_sequence(
            cls.env,
            cls.common_sequence_values
            | {
                "name": "Sequencia Arquivo CNAB - Itau 400",
                "code": "Sequencia Arquivo CNAB - Itau 400",
            },
        )

        cls.own_number_seq_itau_400 = create_with_form_ir_sequence(
            cls.env,
            cls.common_sequence_values
            | {
                "name": "Nosso número Itau 400",
                "code": "nosso.numero",
            },
        )

        cls.cnab_seq_itau_240 = create_with_form_ir_sequence(
            cls.env,
            cls.common_sequence_values
            | {
                "name": "Sequencia Arquivo CNAB - Itau 240",
                "code": "Sequencia Arquivo CNAB - Itau 240",
            },
        )

        cls.own_number_seq_itau_240 = create_with_form_ir_sequence(
            cls.env,
            cls.common_sequence_values
            | {
                "name": "Nosso número Itau 240",
                "code": "nosso.numero",
            },
        )

        # Configurção do CNAB
        cls.common_cnab_config_values = {
            "instructions": "Pagavel em qualquer banco ate o vencimento",
            "boleto_modality": "DM",
            "boleto_accept": "S",
            "generate_own_number": True,
            "tariff_charge_account_id": cls.tariff_charge_account,
            "interest_fee_account_id": cls.interest_fee_account,
            "discount_account_id": cls.discount_account,
            "rebate_account_id": cls.rebate_account,
            "not_payment_account_id": cls.not_payment_account,
            "boleto_discount_perc": "1",
            "boleto_interest_perc": "2",
            "boleto_days_protest": "5",
            "boleto_fee_perc": "1",
        }

        cls.cnab_config_cef = create_with_form_l10n_br_cnab_config(
            cls.env,
            cls.common_cnab_config_values
            | {
                "name": "Caixa Economica Federal - CNAB 240 (inbound)",
                "bank_id": cls.env.ref("l10n_br_base.res_bank_104"),
                "payment_method_id": cls.pay_method_type_240,
                "boleto_wallet": "3",
                "boleto_variation": "19",
                "boleto_discount_code_id": cls.env.ref(
                    "l10n_br_account_payment_order.cef_240_boleto_discount_code_2"
                ),
                "boleto_protest_code_id": cls.env.ref(
                    "l10n_br_account_payment_order.cef_240_boleto_protest_code_1"
                ),
                "boleto_interest_code": "2",
                "cnab_sequence_id": cls.cnab_seq_cef,
                "own_number_sequence_id": cls.own_number_seq_cef,
                "cnab_company_bank_code": "000122",
                "sending_code_id": cls.env.ref(
                    "l10n_br_account_payment_order.cef_240_instruction_01"
                ),
                "write_off_code_id": cls.env.ref(
                    "l10n_br_account_payment_order.cef_240_instruction_02"
                ),
                "change_title_value_code_id": cls.env.ref(
                    "l10n_br_account_payment_order.cef_240_instruction_47"
                ),
                "change_maturity_date_code_id": cls.env.ref(
                    "l10n_br_account_payment_order.cef_240_instruction_06"
                ),
                "protest_title_code_id": cls.env.ref(
                    "l10n_br_account_payment_order.cef_240_instruction_09"
                ),
                "suspend_protest_keep_wallet_code_id": cls.env.ref(
                    "l10n_br_account_payment_order.cef_240_instruction_11"
                ),
                "suspend_protest_write_off_code_id": cls.env.ref(
                    "l10n_br_account_payment_order.cef_240_instruction_10"
                ),
                "grant_rebate_code_id": cls.env.ref(
                    "l10n_br_account_payment_order.cef_240_instruction_04"
                ),
                "cancel_rebate_code_id": cls.env.ref(
                    "l10n_br_account_payment_order.cef_240_instruction_05"
                ),
                "grant_discount_code_id": cls.env.ref(
                    "l10n_br_account_payment_order.cef_240_instruction_07"
                ),
                "cancel_discount_code_id": cls.env.ref(
                    "l10n_br_account_payment_order.cef_240_instruction_08"
                ),
            },
        )

        # TODO: Verificar a possibilidade de incluir um campo to tipo many2many
        #  com o Form, tentei [(6,0,[178, 203])], l10n_br_cnab.code(178, 179),
        #  [178, 203] o erro que retorna:
        #
        #  odoo/tests/common.py", line 2350, in __setattr__
        #  assert descr['type'] not in ('many2many', 'one2many'), \
        #  AssertionError: Can't set an o2m or m2m field, manipulate the
        #  corresponding proxies
        cls.cnab_config_cef.write(
            {
                "liq_return_move_code_ids": [
                    (
                        6,
                        0,
                        [
                            cls.env.ref(
                                "l10n_br_account_payment_order.cef_240_return_06"
                            ).id,
                            cls.env.ref(
                                "l10n_br_account_payment_order.cef_240_return_46"
                            ).id,
                        ],
                    )
                ],
            }
        )

        cls.cnab_config_itau_400 = create_with_form_l10n_br_cnab_config(
            cls.env,
            cls.common_cnab_config_values
            | {
                "name": "Banco ITAÚ - CNAB 400 (inbound)",
                "bank_id": cls.env.ref("l10n_br_base.res_bank_341"),
                "payment_method_id": cls.pay_method_type_400,
                "boleto_wallet": "175",
                "boleto_variation": "19",
                "boleto_interest_code": "2",
                "cnab_sequence_id": cls.cnab_seq_itau_400,
                "own_number_sequence_id": cls.own_number_seq_itau_400,
                "cnab_company_bank_code": "12345",
                "sending_code_id": cls.env.ref(
                    "l10n_br_account_payment_order.itau_400_instruction_01"
                ),
                "write_off_code_id": cls.env.ref(
                    "l10n_br_account_payment_order.itau_400_instruction_02"
                ),
            },
        )

        cls.cnab_config_itau_240 = create_with_form_l10n_br_cnab_config(
            cls.env,
            cls.common_cnab_config_values
            | {
                "name": "Banco ITAÚ - CNAB 240 (inbound)",
                "bank_id": cls.env.ref("l10n_br_base.res_bank_341"),
                "payment_method_id": cls.pay_method_type_240,
                "boleto_wallet": "3",
                "boleto_variation": "19",
                "boleto_protest_code_id": cls.env.ref(
                    "l10n_br_account_payment_order.itau_240_boleto_protest_code_2"
                ),
                "boleto_interest_code": "2",
                "cnab_sequence_id": cls.cnab_seq_itau_240,
                "own_number_sequence_id": cls.own_number_seq_itau_240,
                "cnab_company_bank_code": "12345",
                "sending_code_id": cls.env.ref(
                    "l10n_br_account_payment_order.itau_240_instruction_01"
                ),
                "write_off_code_id": cls.env.ref(
                    "l10n_br_account_payment_order.itau_240_instruction_02"
                ),
            },
        )

        # Diário
        cls.journal_cef = create_with_form_account_journal(
            cls.env,
            {
                "name": "Banco Caixa Economica Federal",
                "type": "bank",
                "code": "BNC6",
                "bank_account_id": cls.bank_account_cef,
                "edi_format_ids": False,
            },
            [
                {
                    "name": "CEF CNAB 240",
                    "payment_method_id": cls.pay_method_type_240,
                }
            ],
        )

        cls.journal_itau_400 = create_with_form_account_journal(
            cls.env,
            {
                "name": "Banco Itau CNAB 400",
                "type": "bank",
                "code": "BNC4",
                "bank_account_id": cls.bank_account_itau,
                "edi_format_ids": False,
            },
            [
                {
                    "name": "Itau CNAB 400",
                    "payment_method_id": cls.pay_method_type_400,
                }
            ],
        )

        cls.journal_itau_240 = create_with_form_account_journal(
            cls.env,
            {
                "name": "Banco Itau CNAB 240",
                "type": "bank",
                "code": "BNC5",
                "bank_account_id": cls.bank_account_itau,
                "edi_format_ids": False,
            },
            [
                {
                    "name": "Itau CNAB 240",
                    "payment_method_id": cls.pay_method_type_240,
                }
            ],
        )

        # Modo de Pagamento
        cls.common_pay_mode_values = {
            "bank_account_link": "fixed",
            "payment_order_ok": True,
            "auto_create_payment_order": True,
            "group_lines": False,
        }

        cls.pay_mode_cef = create_with_form_account_payment_mode(
            cls.env,
            cls.common_pay_mode_values
            | {
                "name": "Cobrança Caixa Economica Federal 240",
                "bank_id": cls.env.ref("l10n_br_base.res_bank_104"),
                "fixed_journal_id": cls.journal_cef,
                "payment_method_id": cls.pay_method_type_240,
                "cnab_config_id": cls.cnab_config_cef,
            },
        )

        cls.pay_mode_itau_400 = create_with_form_account_payment_mode(
            cls.env,
            cls.common_pay_mode_values
            | {
                "name": "Cobrança Itau 400",
                "bank_id": cls.env.ref("l10n_br_base.res_bank_341"),
                "fixed_journal_id": cls.journal_itau_400,
                "payment_method_id": cls.pay_method_type_400,
                "cnab_config_id": cls.cnab_config_itau_400,
            },
        )

        cls.pay_mode_itau_240 = create_with_form_account_payment_mode(
            cls.env,
            cls.common_pay_mode_values
            | {
                "name": "Cobrança Itau 240",
                "bank_id": cls.env.ref("l10n_br_base.res_bank_341"),
                "fixed_journal_id": cls.journal_itau_240,
                "payment_method_id": cls.pay_method_type_240,
                "cnab_config_id": cls.cnab_config_itau_240,
            },
        )

        # Fatura
        cls.inv_common_values = {
            "invoice_payment_term_id": cls.pay_terms_b,
            "partner_id": cls.partner_a,
            "instructions": "TESTE Intruções Boleto",
        }
        cls.inv_line_common_values = {
            "product_id": cls.product_a,
            "price_unit": 1000.0,
            "quantity": 1.0,
            "account_id": cls.income_products_account,
        }

        cls.invoice_cef_240 = create_with_form_account_move(
            cls.env,
            cls.inv_common_values
            | {
                "name": "Teste Caixa Economica Federal CNAB240",
                "payment_mode_id": cls.pay_mode_cef,
            },
            cls.inv_line_common_values,
        )
        # Altera o valor total para 1000
        for line in cls.invoice_cef_240.invoice_line_ids:
            line.tax_ids = False

        cls.invoice_itau_400 = create_with_form_account_move(
            cls.env,
            cls.inv_common_values
            | {
                "name": "Itau CNAB 400",
                "payment_mode_id": cls.pay_mode_itau_400,
            },
            cls.inv_line_common_values,
        )

        cls.invoice_itau_240 = create_with_form_account_move(
            cls.env,
            cls.inv_common_values
            | {
                "name": "Itau CNAB 240",
                "payment_mode_id": cls.pay_mode_itau_240,
            },
            cls.inv_line_common_values,
        )

        # Caso que não é um CNAB
        # Diário Cheque
        cls.journal_cheque = create_with_form_account_journal(
            cls.env,
            {
                "name": "Diário Cheque",
                "type": "cash",
                "code": "DCQ",
                "company_id": cls.env.company,
                "edi_format_ids": False,
                "default_account_id": cls.income_products_account,
            },
            [
                {
                    "name": "Cheque",
                    "payment_method_id": cls.pay_method_manual_test,
                }
            ],
        )

        # Modo de Pagamento
        cls.pay_mode_cheque = create_with_form_account_payment_mode(
            cls.env,
            {
                "name": "Cheque",
                "bank_account_link": "fixed",
                "fixed_journal_id": cls.journal_cheque,
                "payment_method_id": cls.pay_method_manual_test,
                "group_lines": False,
            },
        )

        cls.invoice_cheque = create_with_form_account_move(
            cls.env,
            cls.inv_common_values
            | {
                "name": "Caso Não CNAB",
                "payment_mode_id": cls.pay_mode_cheque,
            },
            cls.inv_line_common_values,
        )

        # Caso Sem Modo de Pagamento
        cls.invoice_without_pay_mode = create_with_form_account_move(
            cls.env,
            cls.inv_common_values
            | {
                "name": "Caso Sem Modo de Pagamento",
            },
            cls.inv_line_common_values,
        )

        # Testa o envio de multiplas Instruções CNAB

        # Apenas para evitar erro no pre-commit
        suspend_protest_keep_wallet = (
            cls.cnab_config_cef.suspend_protest_keep_wallet_code_id
        )
        cls.changes_to_sending = [
            {
                "change_to_send": "change_date_maturity",
                "code_to_check": cls.cnab_config_cef.change_maturity_date_code_id,
            },
            {
                "change_to_send": "grant_rebate",
                "code_to_check": cls.cnab_config_cef.grant_rebate_code_id,
            },
            {
                "change_to_send": "grant_discount",
                "code_to_check": cls.cnab_config_cef.grant_discount_code_id,
            },
            {
                "change_to_send": "cancel_rebate",
                "code_to_check": cls.cnab_config_cef.cancel_rebate_code_id,
            },
            {
                "change_to_send": "cancel_discount",
                "code_to_check": cls.cnab_config_cef.cancel_discount_code_id,
            },
            {
                "change_to_send": "protest_tittle",
                "code_to_check": cls.cnab_config_cef.protest_title_code_id,
            },
            {
                "change_to_send": "suspend_protest_keep_wallet",
                "code_to_check": suspend_protest_keep_wallet,
            },
            {
                "change_to_send": "not_payment",
                "code_to_check": False,
            },
        ]

    def _invoice_confirm_workflow(self, invoice):
        self.assertIn(invoice.state, ["draft", "cancel"])
        invoice.action_post()
        self.assertEqual(invoice.state, "posted")
        invoice.view_boleto_pdf()

    def _run_payment_order_workflow(self, payment_order, test_not_create_file=True):
        """Run all Payment Order Workflow"""
        # Verifica os campos CNAB na linhas de pagamentos
        assert payment_order.payment_line_ids.mapped(
            "own_number"
        ), "own_number field is not filled in Payment Line."
        assert payment_order.payment_line_ids.mapped(
            "instruction_move_code_id"
        ), "instruction_move_code_id field are not filled in Payment Line."

        payment_order.draft2open()
        payment_order.with_context(
            test_not_create_file=test_not_create_file
        ).open2generated()
        payment_order.generated2uploaded()

    def _get_draft_payment_order(self, invoice):
        """Search for the payment order related to the invoice"""
        payment_order = self.env["account.payment.order"].search(
            [
                ("state", "=", "draft"),
                ("payment_mode_id", "=", invoice.payment_mode_id.id),
            ]
        )
        assert payment_order, "Payment Order not created."
        return payment_order

    def _run_invoice_and_order_workflow(self, invoice, test_not_create_file=True):
        self._invoice_confirm_workflow(invoice)
        payment_order = self._get_draft_payment_order(invoice)
        self._run_payment_order_workflow(payment_order, test_not_create_file)

    def import_with_po_wizard(self, payment_mode_id, payment_type="inbound", aml=False):
        order_vals = {
            "payment_type": payment_type,
            "payment_mode_id": payment_mode_id.id,
        }
        order = self.env["account.payment.order"].create(order_vals)
        with self.assertRaises(UserError):
            order.draft2open()
        order.payment_mode_id_change()
        self.assertEqual(order.journal_id.id, payment_mode_id.fixed_journal_id.id)
        self.assertEqual(len(order.payment_line_ids), 0)

        with self.assertRaises(UserError):
            order.draft2open()

        line_create = (
            self.env["account.payment.line.create"]
            .with_context(active_model="account.payment.order", active_id=order.id)
            .create(
                {"date_type": "move", "move_date": Date.context_today(self.env.user)}
            )
        )
        line_create.payment_mode = "same"
        line_create.move_line_filters_change()
        line_create.populate()
        line_create.create_payment_lines()
        line_created_due = (
            self.env["account.payment.line.create"]
            .with_context(active_model="account.payment.order", active_id=order.id)
            .create(
                {
                    "date_type": "due",
                    "target_move": "all",
                    "due_date": Date.context_today(self.env.user),
                }
            )
        )
        line_created_due.populate()
        line_created_due.create_payment_lines()
        self.assertGreater(len(order.payment_line_ids), 0)
        self._run_payment_order_workflow(order)
        self.assertEqual(order.state, "uploaded")
        return order

    def _send_new_cnab_code(
        self,
        aml_to_change,
        code_to_send,
        warning_error=False,
        test_dates_are_equals=False,
    ):
        with Form(
            self.env["account.move.line.cnab.change"].with_context(
                **dict(
                    active_ids=aml_to_change.ids,
                    active_model="account.move.line",
                )
            ),
        ) as f:
            f.change_type = code_to_send
            if code_to_send == "change_date_maturity":
                new_date = date.today() + relativedelta(years=1)

                if warning_error and test_dates_are_equals:
                    # Testa caso Sem Codigo
                    new_date = aml_to_change.date_maturity
                # Testa caso com Codigo e Data de Vencimento igual
                f.date_maturity = new_date
            if code_to_send == "grant_rebate":
                f.rebate_value = 10.00
            if code_to_send == "grant_discount":
                f.discount_value = 10.00

        change_wizard = f.save()

        if warning_error:
            with self.assertRaises(UserError):
                change_wizard.doit()
        else:
            change_wizard.doit()

    def _send_new_cnab_instruction_code(
        self,
        invoice,
        code_to_send,
        code_to_check=False,
        warning_error=False,
        test_not_create_file=True,
    ):
        aml_to_change = invoice.due_line_ids[0]
        self._send_new_cnab_code(aml_to_change, code_to_send, warning_error)

        if not warning_error:
            pay_order_with_new_instruction = self._get_draft_payment_order(
                aml_to_change.move_id
            )
            self._run_payment_order_workflow(
                pay_order_with_new_instruction,
                test_not_create_file,
            )

            if code_to_check:
                for line in pay_order_with_new_instruction.payment_line_ids:
                    self.assertEqual(
                        line.instruction_move_code_id.name,
                        code_to_check.name,
                    )
            if code_to_send == "change_date_maturity":
                new_date = date.today() + relativedelta(years=1)
                self.assertEqual(
                    aml_to_change.date_maturity,
                    new_date,
                    "Data não alterada",
                )
            if code_to_send == "not_payment":
                self.assertEqual(aml_to_change.payment_situation, "nao_pagamento")
                self.assertEqual(aml_to_change.cnab_state, "done")
                self.assertEqual(aml_to_change.reconciled, True)

    def _make_payment(self, invoice, value):
        journal_cash = self.journal_cheque
        payment_register = Form(
            self.env["account.payment.register"].with_context(
                active_model="account.move",
                active_ids=invoice.ids,
            )
        )
        payment_register.journal_id = journal_cash
        method_lines = journal_cash._get_available_payment_method_lines(
            "inbound"
        ).filtered(lambda x: x.code == "manual")
        payment_register.payment_method_line_id = method_lines[0]
        payment_register.amount = value
        return payment_register.save()._create_payments()

    def _check_order_with_write_off_code(self, invoice):
        payment_order = self._get_draft_payment_order(invoice)
        self.assertEqual(
            payment_order.cnab_config_id.write_off_code_id,
            payment_order.payment_line_ids.mapped("instruction_move_code_id"),
            "Payment Order with wrong instruction_move_code_id for Write Off",
        )
        # TODO: Pedido de Baixa está indo com o valor inicial deveria ser
        #  o ultimo valor enviado ? Já que é um Pedido de Baixa o Banco
        #  validaria essas atualizações ?
