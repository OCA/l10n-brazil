# Copyright (C) 2021-Today - Akretion (<http://www.akretion.com>).
# @author Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import os

from odoo.exceptions import UserError
from odoo.tests import tagged

from odoo.addons.l10n_br_account_payment_brcobranca.tests.common import (
    TestBRCobrancaCommon,
)


@tagged("post_install", "-at_install")
class TestPaymentOrder(TestBRCobrancaCommon):
    def test_banco_brasil_cnab_400(self):
        """Teste Boleto e Remessa Banco do Brasil - CNAB 400"""
        self._run_invoice_and_order_brcobranca(self.invoice_brasil_400)

    def test_banco_itau_cnab_400(self):
        """Teste Boleto e Remessa Banco Itau - CNAB 400"""
        self._run_invoice_and_order_brcobranca(self.invoice_itau_400)

    def test_banco_bradesco_cnab_400(self):
        """Teste Boleto e Remessa Banco Bradesco - CNAB 400"""
        self._run_invoice_and_order_brcobranca(self.invoice_bradesco_400)

    def test_banco_sicred_cnab_240(self):
        """Teste Boleto e Remessa Banco SICREDI - CNAB 240"""
        self._run_invoice_and_order_brcobranca(self.invoice_sicredi_240)

    def test_banco_santander_cnab_400(self):
        """Teste Boleto e Remessa Banco Santander - CNAB 400"""
        self._run_invoice_and_order_brcobranca(self.invoice_santander_400)

    def test_banco_santander_cnab_240(self):
        """Teste Boleto e Remessa Banco Santander - CNAB 240"""
        self._run_invoice_and_order_brcobranca(self.invoice_santander_240)

    def test_bank_cnab_not_implement_brcobranca(self):
        """Test Bank CNAB not implemented in BRCobranca."""
        self.invoice_itau_240.action_post()
        self.assertEqual(self.invoice_itau_240.state, "posted")
        # O Banco Itau CNAB 240 não está implementado no BRCobranca
        # por isso deve gerar erro.
        if not os.environ.get("CI_NO_BRCOBRANCA"):
            with self.assertRaises(UserError):
                self.invoice_itau_240.view_boleto_pdf()

    def test_payment_order_invoice_cancel_process(self):
        """Test Payment Order and Invoice Cancel process."""

        if not self._check_ci_no_brcobranca():
            self._run_invoice_and_order_brcobranca(self.invoice_cef_240)
            payment_order = self.env["account.payment.order"].search(
                [("payment_mode_id", "=", self.invoice_cef_240.payment_mode_id.id)]
            )

            # Ordem de Pagto CNAB não pode ser apagada
            with self.assertRaises(UserError):
                payment_order.unlink()

            # Ordem de Pagto CNAB não pode ser Cancelada
            with self.assertRaises(UserError):
                payment_order.action_done_cancel()

            # Testar Cancelamento
            self.invoice_cef_240.button_cancel()

            # Caso de Ordem de Pagamento já confirmado a Linha
            # e a account.move não pode ser apagadas
            self.assertEqual(len(payment_order.payment_line_ids), 2)
            # A partir da v13 as account.move.line relacionadas continuam existindo
            self.assertEqual(len(self.invoice_cef_240.line_ids), 3)
            self.assertEqual(len(self.invoice_cef_240.invoice_line_ids), 1)

            # Criação do Pedido de Baixa
            self._check_order_with_write_off_code(self.invoice_cef_240)

    def test_payment_outside_cnab_writeoff_and_change_tittle_value(self):
        """
        Caso de Pagamento com CNAB já iniciado sendo necessário fazer a Baixa
        de uma Parcela e a Alteração de Valor de Titulo por pagto parcial.
        """
        if not self._check_ci_no_brcobranca():
            self._run_invoice_and_order_brcobranca(self.invoice_cef_240)
            self._make_payment(self.invoice_cef_240, 600)
            payment_order = self._get_draft_payment_order(self.invoice_cef_240)
            for line in payment_order.payment_line_ids:
                if line.amount_currency == 300:
                    # Caso de Baixa do Titulo
                    self.assertEqual(
                        line.instruction_move_code_id,
                        line.order_id.cnab_config_id.write_off_code_id,
                    )
                else:
                    # Caso de alteração do valor do titulo por pagamento parcial
                    self.assertEqual(
                        line.instruction_move_code_id,
                        line.order_id.cnab_config_id.change_title_value_code_id,
                    )
                    self.assertEqual(
                        line.move_line_id.amount_residual, line.amount_currency
                    )

    def test_cnab_workflow_with_multiple_instructions(self):
        """
        Test sending multiple CNAB Instructions Code
        """
        if not self._check_ci_no_brcobranca():
            self._run_invoice_and_order_brcobranca(self.invoice_cef_240)
            for change in self.changes_to_sending:
                self._send_new_cnab_instruction_code(
                    self.invoice_cef_240,
                    change.get("change_to_send"),
                    change.get("code_to_check"),
                    test_not_create_file=False,
                )

    def test_cnab_change_method_not_payment(self):
        """
        Test CNAB Change Method Not Payment
        """
        if not self._check_ci_no_brcobranca():
            self._run_invoice_and_order_brcobranca(self.invoice_cef_240)
            aml_to_change = self.invoice_cef_240.due_line_ids[0]
            self._send_new_cnab_code(aml_to_change, "not_payment")
            self.assertEqual(aml_to_change.payment_situation, "nao_pagamento")
            self.assertEqual(aml_to_change.cnab_state, "done")
            self.assertEqual(aml_to_change.reconciled, True)
            self._check_order_with_write_off_code(self.invoice_cef_240)

    def test_make_payment_outside_cnab(self):
        """
        Caso de Pagamento com CNAB
        """
        if not self._check_ci_no_brcobranca():
            self._run_invoice_and_order_brcobranca(self.invoice_cef_240)
            self._make_payment(self.invoice_cef_240, 100)
            payment_order = self._get_draft_payment_order(self.invoice_cef_240)
            for line in payment_order.payment_line_ids:
                self.assertEqual(
                    line.instruction_move_code_id.name,
                    self.cnab_config_cef.change_title_value_code_id.name,
                )
            self._run_payment_order_workflow(payment_order, False)

            self._make_payment(self.invoice_cef_240, 100)
            payment_order = self._get_draft_payment_order(self.invoice_cef_240)
            for line in payment_order.payment_line_ids:
                # Caso de alteração do valor do titulo por pagamento parcial
                self.assertEqual(
                    line.instruction_move_code_id,
                    line.order_id.cnab_config_id.change_title_value_code_id,
                )
                self.assertEqual(
                    line.move_line_id.amount_residual, line.amount_currency
                )

            self._run_payment_order_workflow(payment_order, False)
            for line in payment_order.payment_line_ids:
                self.assertEqual(
                    line.move_line_id.amount_residual, line.amount_currency
                )

            # Perform the payment of Amount Residual to Write Off
            self._make_payment(
                self.invoice_cef_240, self.invoice_cef_240.amount_residual
            )

            # Ordem de Pagto com alterações
            payment_order = self._get_draft_payment_order(self.invoice_cef_240)
            self._check_order_with_write_off_code(self.invoice_cef_240)

    def test_1_unicred_cnab400_valor_menor(self):
        """
        Test UNICRED CNAB 400 'Boleto, Arquivo de Remessa' and import two 'Arquivo
        de Retorno' the first to Confirm the CNAB Instruction, only generate a LOG,
        and the second for generate the Payment when the received Value are less
        than Debit in Odoo.
        """

        if not self._check_ci_no_brcobranca():
            self._run_invoice_and_order_workflow(self.invoice_unicred_400_1)
            log = self._run_import_return_file(
                "CNAB400UNICRED_valor_menor_1.RET",
                self.journal_unicred,
            )

            self.assertEqual("Banco UNICRED - Conta 372", log.name)

            # Importando o segundo arquivo que gera o Pagamento
            moves = self._run_import_return_file(
                "CNAB400UNICRED_valor_menor_2.RET",
                self.journal_unicred,
            )

            self.assertEqual("Retorno CNAB - Banco UNICRED - Conta 372", moves.ref)
            self.assertEqual(self.invoice_unicred_400_1.payment_state, "paid")

    def test_2_unicred_cnab400_valor_maior(self):
        """
        Test UNICRED CNAB 400 'Boleto, Arquivo de Remessa' and import two 'Arquivo
        de Retorno' the first to Confirm the CNAB Instruction, only generate a LOG,
        and the second for generate the Payment when the received Value are greater
        than Debit in Odoo.
        """

        if not self._check_ci_no_brcobranca():
            self._run_invoice_and_order_brcobranca(self.invoice_unicred_400_2)
            log = self._run_import_return_file(
                "CNAB400UNICRED_valor_maior_3.RET",
                self.journal_unicred,
            )

            self.assertEqual("Banco UNICRED - Conta 372", log.name)

            # Importação do Arquivo que Gera Pagamento
            moves = self._run_import_return_file(
                "CNAB400UNICRED_valor_maior_4.RET",
                self.journal_unicred,
            )
            self.assertEqual("Retorno CNAB - Banco UNICRED - Conta 372", moves.ref)
            self.assertEqual(self.invoice_unicred_400_2.payment_state, "paid")

    def test_3_ailos_cnab_240(self):
        """
        Test AILOS CNAB 240 'Boleto, Arquivo de Remessa' and import one
        'Arquivo de Retorno' for generate the Payment.
        """

        if not self._check_ci_no_brcobranca():
            self._run_invoice_and_order_brcobranca(self.invoice_ailos_240)
            moves = self._run_import_return_file(
                "CNAB240AILOS.RET",
                self.journal_ailos,
            )
            self.assertEqual(
                "Retorno CNAB - Banco COOP CENTRAL AILOS - Conta 374", moves.ref
            )
            self.assertEqual(self.invoice_ailos_240.payment_state, "paid")

    def test_5_nordeste_cnab_400(self):
        """
        Test import Nordeste Bank CNAB 400, the case has different 'Return Code'
        for refused 'Instruction Code'.
        """

        if not self._check_ci_no_brcobranca():
            self._run_invoice_and_order_brcobranca(self.invoice_nordeste_400)
            log = self._run_import_return_file(
                "CNAB400NORDESTE.RET",
                self.journal_nordeste,
            )
            for line in log.event_ids:
                self.assertEqual("51-Entrada Rejeitada.", line.occurrences)
                self.assertEqual("not_accepted", line.move_line_id.cnab_state)
