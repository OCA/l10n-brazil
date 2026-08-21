# Copyright (C) 2021-Today - Akretion (<http://www.akretion.com>).
# @author Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
import os
from datetime import date, timedelta
from unittest.mock import patch

from erpbrasil.base import misc

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests import tagged

from odoo.addons.l10n_br_account_payment_brcobranca.constants.br_cobranca import (
    get_brcobranca_bank,
    modulo11,
)
from odoo.addons.l10n_br_account_payment_brcobranca.tests.common import (
    TestBRCobrancaCommon,
)


@tagged("post_install", "-at_install")
class TestPaymentOrder(TestBRCobrancaCommon):
    def test_banco_brasil_cnab_400(self):
        """Teste Boleto e Remessa Banco do Brasil - CNAB 400"""
        self._run_invoice_and_order_brcobranca(self.invoice_brasil_400)

    def test_banco_brasil_cnab_240(self):
        """Teste Boleto e Remessa Banco do Brasil - CNAB 240"""
        self._run_invoice_and_order_brcobranca(self.invoice_brasil_240)

    def test_banco_itau_cnab_400(self):
        """Teste Boleto e Remessa Banco Itau - CNAB 400"""
        self._run_invoice_and_order_brcobranca(self.invoice_itau_400)

    def test_banco_bradesco_cnab_400(self):
        """Teste Boleto e Remessa Banco Bradesco - CNAB 400"""
        self._run_invoice_and_order_brcobranca(self.invoice_bradesco_400)

    def test_banco_sicred_cnab_240(self):
        """Teste Boleto e Remessa Banco SICREDI - CNAB 240"""
        self._run_invoice_and_order_brcobranca(self.invoice_sicredi_240)

    def test_banco_sicred_cnab_240_file_name(self):
        """Teste da nomenclatura do arquivo de remessa SICREDI - CNAB 240.

        Manual Sicredi CNAB 240 - item 6.1 (Nomenclatura dos arquivos):
        arquivo de remessa no formato CCCCCMDD.XXX, onde CCCCC = Código do
        beneficiário, MDD = Código do mês e nº do dia da data de geração e
        XXX = extensão de uso livre (sugestão do manual: 001, 002, etc).
        """
        self.invoice_sicredi_240.action_post()
        payment_order = self._get_draft_payment_order(self.invoice_sicredi_240)
        payment_order.file_number = 1

        bank_account_id = payment_order.journal_id.bank_account_id
        context_today = fields.Date.context_today(payment_order)
        month_code = str(context_today.month)
        if context_today.month == 10:
            month_code = "O"
        elif context_today.month == 11:
            month_code = "N"
        elif context_today.month == 12:
            month_code = "D"

        expected_file_name = (
            misc.punctuation_rm(bank_account_id.acc_number).zfill(5)
            + month_code
            + context_today.strftime("%d")
            + ".001"
        )
        self.assertEqual(payment_order.get_file_name("240"), expected_file_name)
        self.assertRegex(
            payment_order.get_file_name("240"), r"^\d{5}[1-9OND]\d{2}\.\d{3}$"
        )

    def test_banco_sicred_cnab_240_file_name_update_header(self):
        """Alterar o nome do arquivo deve regenerar o header do CNAB.

        Mantém o comportamento anterior em que, ao alterar o nome do arquivo
        (nº sequencial / file_number), o header do arquivo CNAB e o anexo
        são regenerados com o novo número.
        """
        self.invoice_sicredi_240.action_post()
        payment_order = self._get_draft_payment_order(self.invoice_sicredi_240)

        def _fake_remessa(bank_brcobranca, remessa_values, cnab_type):
            return str(remessa_values["sequencial_remessa"]).zfill(6).encode()

        with patch.object(
            type(payment_order),
            "_get_brcobranca_remessa",
            side_effect=_fake_remessa,
        ):
            payment_order.draft2open()
            payment_order.with_context(
                test_not_create_file=False
            ).open2generated()
            self.assertEqual(payment_order.state, "generated")
            # A sequência é consumida apenas na confirmação de envio,
            # permitindo que o usuário edite o número antes de confirmar.
            self.assertEqual(payment_order.file_number, 0)

            # Ao alterar o nome do arquivo (file_number) o header do
            # CNAB e o anexo são regenerados com o novo número.
            payment_order.file_number = 7

            self.assertEqual(
                payment_order.cnab_file, base64.b64encode(b"000007")
            )
            self.assertTrue(payment_order.cnab_filename.endswith(".007"))
            self.assertRegex(
                payment_order.cnab_filename, r"^\d{5}[1-9OND]\d{2}\.\d{3}$"
            )

    def test_banco_sicred_cnab_240_header_date(self):
        """A data de geração do header do CNAB 240 deve usar a data do usuário.

        A API BRCobranca grava a data de geração usando o fuso do servidor
        onde ela roda, que pode ser diferente do fuso do usuário do Odoo,
        fazendo o header não conferir com o nome do arquivo e a data de
        processamento (Manual Sicredi CNAB 240 - itens 6.1 e 6.4).
        """
        self.invoice_sicredi_240.action_post()
        payment_order = self._get_draft_payment_order(self.invoice_sicredi_240)
        context_today = fields.Date.context_today(payment_order)

        # Simula a data gerada pela API BRCobranca no fuso do servidor,
        # um dia à frente da data do usuário.
        wrong_date = (context_today + timedelta(days=1)).strftime("%d%m%Y")
        header = b"X" * 143 + wrong_date.encode() + b"Y" * 89
        fake_remessa = header + b"\r\n"

        fixed = payment_order._fix_remessa_header_date(fake_remessa, "240")
        expected = (
            fake_remessa[:143]
            + context_today.strftime("%d%m%Y").encode()
            + fake_remessa[151:]
        )
        self.assertEqual(fixed, expected)

        # A data corrigida deve ser a data do usuário (posições 144-151).
        self.assertEqual(fixed[143:151], context_today.strftime("%d%m%Y").encode())

        # CNAB 400 não deve ser alterado.
        self.assertEqual(
            payment_order._fix_remessa_header_date(fake_remessa, "400"),
            fake_remessa,
        )

    def test_banco_sicred_cnab_240_prepare_payment_line(self):
        """Teste da preparação das linhas de pagamento SICREDI - CNAB 240.

        Não depende da API externa do BRCobranca.
        """
        self.invoice_sicredi_240.action_post()
        self.assertEqual(self.invoice_sicredi_240.state, "posted")
        payment_order = self._get_draft_payment_order(self.invoice_sicredi_240)
        self.assertTrue(payment_order.payment_line_ids)

        bank_account_id = payment_order.journal_id.bank_account_id
        bank_brcobranca = get_brcobranca_bank(bank_account_id, "240")

        for line in payment_order.payment_line_ids:
            # O campo date é preenchido no fluxo draft2open, necessário
            # para o _prepare_boleto_line_vals da base.
            if not line.date:
                line.date = fields.Date.context_today(line)
            prepared = line.prepare_bank_payment_line(bank_brcobranca)
            cnab_config = line.order_id.payment_mode_id.cnab_config_id
            sequencial = "".join(
                ch for ch in str(line.own_number) if ch.isdigit()
            ).zfill(5)[-5:]
            # Base do DV: agência + posto + beneficiário + ano + byte + sequencial
            # (5 dígitos, com zeros à esquerda - Manual Sicredi item 4.5)
            base_dv = (
                bank_account_id.bra_number
                + str(cnab_config.boleto_post).zfill(2)
                + misc.punctuation_rm(bank_account_id.acc_number).zfill(5)
                + str(date.today().year)[2:]
                + str(cnab_config.boleto_byte_idt)
                + sequencial
            )
            expected_nosso_numero = (
                str(date.today().year)[2:]
                + str(cnab_config.boleto_byte_idt)
                + sequencial
                + str(modulo11(base_dv, 9, 0))
            )
            # Nosso Número no formato AA/BXXXXX-D (Manual Sicredi itens 4.4 e 4.5),
            # sem os separadores "/" e "-" que são apenas de apresentação.
            self.assertEqual(prepared["nosso_numero"], expected_nosso_numero)
            self.assertRegex(prepared["nosso_numero"], r"^\d{9}$")
            # Multa nunca deve ser preenchida como 0 no Sicredi
            self.assertNotEqual(prepared.get("codigo_multa"), "0")
            # A configuração padrão define boleto_discount_perc, portanto a
            # linha possui desconto e o código enviado é o esperado (1 = Valor Fixo).
            self.assertEqual(prepared.get("cod_desconto"), "1")
            # Segmento Q: posições 114-128 são CNAB (Manual Sicredi item 8.5),
            # o bairro do pagador deve ser enviado em branco
            self.assertEqual(prepared.get("bairro_sacado"), "")

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
            with self.assertRaises(UserError):
                self._run_import_return_file(
                    "CNAB400UNICRED_valor_maior_4.RET",
                    self.journal_unicred,
                )

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
