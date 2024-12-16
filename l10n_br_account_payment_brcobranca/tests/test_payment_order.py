# Copyright (C) 2021-Today - Akretion (<http://www.akretion.com>).
# @author Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo.exceptions import UserError
from odoo.tests import tagged

from odoo.addons.l10n_br_account_payment_brcobranca.tests.common import (
    TestBrAccountPaymentOderCommon,
)


@tagged("post_install", "-at_install")
class TestPaymentOrder(TestBrAccountPaymentOderCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Get Invoice for test
        cls.invoice_unicred = cls.env.ref(
            "l10n_br_account_payment_order."
            "demo_invoice_payment_order_unicred_cnab400"
        )
        cls.invoice_cef = cls.env.ref(
            "l10n_br_account_payment_order." "demo_invoice_payment_order_cef_cnab240"
        )
        # I validate invoice by creating on
        cls.invoice_cef.action_post()
        payment_order = cls.env["account.payment.order"].search(
            [("payment_mode_id", "=", cls.invoice_cef.payment_mode_id.id)]
        )
        # Open payment order
        payment_order.draft2open()

        # Verifica se deve testar com o mock
        cls._check_mocked_method(
            cls, payment_order, "teste_remessa-cef_240-1.REM", "open2generated"
        )

        # Confirm Upload
        payment_order.generated2uploaded()

        # Move Line para alterar
        cls.aml_to_change = cls.invoice_cef.financial_move_line_ids[0]

    def test_banco_brasil_cnab_400(self):
        """Teste Boleto e Remessa Banco do Brasil - CNAB 400"""
        invoice_bb_cnab_400 = self.env.ref(
            "l10n_br_account_payment_order.demo_invoice_payment_order_bb_cnab400"
        )
        self._run_boleto_remessa(
            invoice_bb_cnab_400, "boleto_teste_bb400.pdf", "teste_remessa_bb400.REM"
        )

    def test_banco_itau_cnab_400(self):
        """Teste Boleto e Remessa Banco Itau - CNAB 400"""
        invoice_itau_cnab_400 = self.env.ref(
            "l10n_br_account_payment_order.demo_invoice_payment_order_itau_cnab400"
        )
        self._run_boleto_remessa(
            invoice_itau_cnab_400,
            "boleto_teste_itau400.pdf",
            "teste_remessa_itau400.REM",
        )

    def test_banco_bradesco_cnab_400(self):
        """Teste Boleto e Remessa Banco Bradesco - CNAB 400"""
        invoice_bradesco_cnab_400 = self.env.ref(
            "l10n_br_account_payment_order.demo_invoice_payment_order"
        )
        self._run_boleto_remessa(
            invoice_bradesco_cnab_400,
            "boleto_teste_bradesco400.pdf",
            "teste_remessa_bradesco400.REM",
        )

    def test_banco_unicred_cnab_400(self):
        """Teste Boleto e Remessa Banco Unicred - CNAB 400"""
        invoice_unicred_cnab_400 = self.env.ref(
            "l10n_br_account_payment_order.demo_invoice_payment_order_unicred_cnab400"
        )
        self._run_boleto_remessa(
            invoice_unicred_cnab_400,
            "boleto_teste_unicred400.pdf",
            "teste_remessa-unicred_400-1.REM",
        )

    def test_banco_sicred_cnab_240(self):
        """Teste Boleto e Remessa Banco SICREDI - CNAB 240"""
        invoice_sicred_cnab_240 = self.env.ref(
            "l10n_br_account_payment_order.demo_invoice_payment_order_sicredi_cnab240"
        )

        self._run_boleto_remessa(
            invoice_sicred_cnab_240,
            "boleto_teste_sicredi_cnab240.pdf",
            "teste_remessa_sicredi240.REM",
        )

    def test_banco_ailos_cnab_240(self):
        """Teste Boleto e Remessa Banco AILOS - CNAB 240"""
        invoice_ailos_cnab_240 = self.env.ref(
            "l10n_br_account_payment_order.demo_invoice_payment_order_ailos_cnab240"
        )
        self._run_boleto_remessa(
            invoice_ailos_cnab_240,
            "boleto_teste_ailos_cnab240.pdf",
            "teste_remessa_ailos240.REM",
        )

    def test_banco_santander_cnab_400(self):
        """Teste Boleto e Remessa Banco Santander - CNAB 400"""
        invoice_santander_cnab_400 = self.env.ref(
            "l10n_br_account_payment_order.demo_invoice_payment_order_santander_cnab400"
        )
        self._run_boleto_remessa(
            invoice_santander_cnab_400,
            "boleto_teste_santander400.pdf",
            "teste_remessa_santander400.REM",
        )

    def test_banco_santander_cnab_240(self):
        """Teste Boleto e Remessa Banco Santander - CNAB 240"""
        invoice_santander_cnab_240 = self.env.ref(
            "l10n_br_account_payment_order.demo_invoice_payment_order_santander_cnab240"
        )
        self._run_boleto_remessa(
            invoice_santander_cnab_240,
            "boleto_teste_santander240.pdf",
            "teste_remessa_santander240.REM",
        )

    def test_bank_cnab_not_implement_brcobranca(self):
        """Test Bank CNAB not implemented in BRCobranca."""
        invoice = self.env.ref(
            "l10n_br_account_payment_order.demo_invoice_payment_order_itau_cnab240"
        )
        # I validate invoice
        invoice.action_post()

        # I check that the invoice state is "Posted"
        self.assertEqual(invoice.state, "posted")
        # O Banco Itau CNAB 240 não está implementado no BRCobranca
        # por isso deve gerar erro.
        with self.assertRaises(UserError):
            invoice.view_boleto_pdf()

    def test_payment_order_invoice_cancel_process(self):
        """Test Payment Order and Invoice Cancel process."""

        payment_order = self.env["account.payment.order"].search(
            [("payment_mode_id", "=", self.invoice_cef.payment_mode_id.id)]
        )

        # Ordem de Pagto CNAB não pode ser apagada
        with self.assertRaises(UserError):
            payment_order.unlink()

        # Ordem de Pagto CNAB não pode ser Cancelada
        with self.assertRaises(UserError):
            payment_order.action_done_cancel()

        # Testar Cancelamento
        self.invoice_cef.button_cancel()

        # Caso de Ordem de Pagamento já confirmado a Linha
        # e a account.move não pode ser apagadas
        self.assertEqual(len(payment_order.payment_line_ids), 2)
        # A partir da v13 as account.move.line relacionadas
        # continuam exisitindo
        self.assertEqual(len(self.invoice_cef.line_ids), 3)
        self.assertEqual(len(self.invoice_cef.invoice_line_ids), 1)

        # Criação do Pedido de Baixa
        payment_order = self.env["account.payment.order"].search(
            [
                ("payment_mode_id", "=", self.invoice_cef.payment_mode_id.id),
                ("state", "=", "draft"),
            ]
        )

        for line in payment_order.payment_line_ids:
            # Caso de Baixa do Titulo
            self.assertEqual(
                line.instruction_move_code_id.name,
                line.order_id.cnab_config_id.write_off_code_id.name,
            )

    def test_payment_outside_cnab_writeoff_and_change_tittle_value(self):
        """
        Caso de Pagamento com CNAB já iniciado sendo necessário fazer a Baixa
        de uma Parcela e a Alteração de Valor de Titulo por pagto parcial.
        """
        self._make_payment(self.invoice_cef, 600)
        # Ordem de PAgto com alterações
        payment_order = self.env["account.payment.order"].search(
            [
                ("payment_mode_id", "=", self.invoice_cef.payment_mode_id.id),
                ("state", "=", "draft"),
            ]
        )
        for line in payment_order.payment_line_ids:
            if line.amount_currency == 300:
                # Caso de Baixa do Titulo
                self.assertEqual(
                    line.instruction_move_code_id.name,
                    line.order_id.cnab_config_id.write_off_code_id.name,
                )
            else:
                # Caso de alteração do valor do titulo por pagamento parcial
                self.assertEqual(
                    line.instruction_move_code_id.name,
                    line.order_id.cnab_config_id.change_title_value_code_id.name,
                )
                self.assertEqual(
                    line.move_line_id.amount_residual, line.amount_currency
                )

    def test_cnab_change_due_date(self):
        """
        Test CNAB Change Due Date
        """
        self._send_new_cnab_code(self.aml_to_change, "change_date_maturity")
        self._run_remessa(
            self.invoice_cef,
            "teste_remessa-cef_240-2-data_venc.REM",
            self.invoice_cef.cnab_config_id.change_maturity_date_code_id,
        )

    def test_cnab_protest(self):
        """
        Test CNAB Protesto
        """
        self._send_new_cnab_code(self.aml_to_change, "protest_tittle")
        self._run_remessa(
            self.invoice_cef,
            "teste_remessa-cef_240-3-protesto.REM",
            self.invoice_cef.cnab_config_id.protest_title_code_id,
        )

    def test_cnab_suspend_protest_and_keep_wallet(self):
        """
        Test CNAB Suspend Protest and Keep Wallet
        """
        self._send_new_cnab_code(self.aml_to_change, "suspend_protest_keep_wallet")
        self._run_remessa(
            self.invoice_cef,
            "teste_remessa-cef_240-4-sust_prot_mant_carteira.REM",
            self.invoice_cef.cnab_config_id.suspend_protest_keep_wallet_code_id,
        )

    def test_cnab_grant_rebate(self):
        """
        Test CNAB Grant Rebate
        """
        self._send_new_cnab_code(self.aml_to_change, "grant_rebate")
        self._run_remessa(
            self.invoice_cef,
            "teste_remessa-cef_240-5-conceder_abatimento.REM",
            self.invoice_cef.cnab_config_id.grant_rebate_code_id,
        )

    def test_cnab_cancel_rebate(self):
        """
        Test CNAB Cancel Rebate
        """
        self._send_new_cnab_code(self.aml_to_change, "cancel_rebate")
        self._run_remessa(
            self.invoice_cef,
            "teste_remessa-cef_240-6-cancelar_abatimento.REM",
            self.invoice_cef.cnab_config_id.cancel_rebate_code_id,
        )

    def test_cnab_grant_discount(self):
        """
        Test CNAB Grant Discount
        """
        self._send_new_cnab_code(self.aml_to_change, "grant_discount")
        self._run_remessa(
            self.invoice_cef,
            "teste_remessa-cef_240-7-conceder_desconto.REM",
            self.invoice_cef.cnab_config_id.grant_discount_code_id,
        )

    def test_cnab_cancel_discount(self):
        """
        Test CNAB Cancel Discount
        """
        self._send_new_cnab_code(self.aml_to_change, "cancel_discount")
        self._run_remessa(
            self.invoice_cef,
            "teste_remessa-cef_240-8-cancelar_desconto.REM",
            self.invoice_cef.cnab_config_id.cancel_discount_code_id,
        )
        # Suspender Protesto e dar Baixa
        # TODO: Especificar melhor esse caso

    def test_cnab_change_method_not_payment(self):
        """
        Test CNAB Change Method Not Payment
        """
        self._send_new_cnab_code(self.aml_to_change, "not_payment")
        self.assertEqual(self.aml_to_change.payment_situation, "nao_pagamento")
        self.assertEqual(self.aml_to_change.cnab_state, "done")
        self.assertEqual(self.aml_to_change.reconciled, True)
        payment_order = self.env["account.payment.order"].search(
            [
                ("payment_mode_id", "=", self.invoice_cef.payment_mode_id.id),
                ("state", "=", "draft"),
            ]
        )
        for line in payment_order.payment_line_ids:
            # Baixa do Titulo
            self.assertEqual(
                line.instruction_move_code_id.name,
                line.order_id.cnab_config_id.write_off_code_id.name,
            )

    def test_payment(self):
        """
        Caso de Pagamento com CNAB
        """
        self._make_payment(self.invoice_cef, 100)

        self._run_remessa(
            self.invoice_cef,
            "teste_remessa-cef_240-9-alt_valor_titulo.REM",
            self.invoice_cef.cnab_config_id.change_title_value_code_id,
        )

        self._make_payment(self.invoice_cef, 100)
        # Ordem de PAgto com alterações
        payment_order = self.env["account.payment.order"].search(
            [
                ("payment_mode_id", "=", self.invoice_cef.payment_mode_id.id),
                ("state", "=", "draft"),
            ]
        )

        for line in payment_order.payment_line_ids:
            # Caso de alteração do valor do titulo por pagamento parcial
            self.assertEqual(
                line.instruction_move_code_id.name,
                line.order_id.cnab_config_id.change_title_value_code_id.name,
            )
            self.assertEqual(line.move_line_id.amount_residual, line.amount_currency)

        # Ordem de PAgto com alterações
        self._run_remessa(
            self.invoice_cef,
            "teste_remessa-cef_240-10-alt_valor_titulo.REM",
            self.invoice_cef.cnab_config_id.change_title_value_code_id,
            check_amount=True,
        )

        # Perform the payment of Amount Residual to Write Off
        self._make_payment(self.invoice_cef, self.invoice_cef.amount_residual)

        # Ordem de PAgto com alterações
        payment_order = self.env["account.payment.order"].search(
            [
                ("payment_mode_id", "=", self.invoice_cef.payment_mode_id.id),
                ("state", "=", "draft"),
            ]
        )
        for line in payment_order.payment_line_ids:
            # Baixa do Titulo
            self.assertEqual(
                line.instruction_move_code_id.name,
                line.order_id.cnab_config_id.write_off_code_id.name,
            )
            # TODO: Pedido de Baixa está indo com o valor inicial deveria ser
            #  o ultimo valor enviado ? Já que é um Pedido de Baixa o Banco
            #  validaria essas atualizações ?
            #  l.move_line_id.amount_residual = 0.0
            #  l.amount_currency = 300
            # self.assertEqual(
            #    l.move_line_id.amount_residual,
            #    l.amount_currency)
