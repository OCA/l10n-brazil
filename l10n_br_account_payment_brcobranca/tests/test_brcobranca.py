# Copyright (C) 2021-Today - Akretion (<http://www.akretion.com>).
# @author Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
import os

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests import tagged

from odoo.addons.l10n_br_account_payment_brcobranca.constants.br_cobranca import (
    get_brcobranca_bank,
    modulo11,
)
from odoo.addons.l10n_br_account_payment_brcobranca.parser.cnab_file_parser import (
    CNABFileParser,
)
from odoo.addons.l10n_br_account_payment_brcobranca.tests.common import (
    TestBRCobrancaCommon,
)

# Dados do Split Payment (IBS/CBS) usados nos testes, veja
# https://github.com/OCA/l10n-brazil/issues/5146 . A chave do Documento Fiscal e
# o ID do split são os mesmos do arquivo de retorno de exemplo.
SPLIT_PAYMENT_DOCUMENT_KEY = "35260647906085000135550010000012341000012345"
SPLIT_PAYMENT_IDENTIFIER = "E2E12345678901234567890123456789012"
# Campo do Evento do Retorno (l10n_br_cnab.return.event) -> (valor esperado,
# campo do JSON do BRCobranca). Os valores são do Segmento X-03 (dados fiscais e
# CBS/IBS) e do Segmento X-04 (valores da liquidação) do Layout Padrão Febraban
# 240 posições V11.0.
SPLIT_PAYMENT_EVENT_VALUES = {
    "split_payment_document_key": (SPLIT_PAYMENT_DOCUMENT_KEY, "documento_fiscal"),
    "split_payment_identifier": (SPLIT_PAYMENT_IDENTIFIER, "id_split"),
    "split_payment_identifier_type": ("E2E", "tipo_id_split"),
    "split_payment_cbs_informed": (1.8, "valor_cbs_informado"),
    "split_payment_ibs_informed": (0.2, "valor_ibs_informado"),
    "split_payment_cbs_corrected": (1.8, "valor_cbs_corrigido"),
    "split_payment_ibs_corrected": (0.2, "valor_ibs_corrigido"),
    "split_payment_cbs_open": (0.0, "valor_cbs_em_aberto"),
    "split_payment_ibs_open": (0.0, "valor_ibs_em_aberto"),
    "split_payment_cbs_segregated": (1.8, "valor_cbs_segregado"),
    "split_payment_ibs_segregated": (0.2, "valor_ibs_segregado"),
    "split_payment_absent_value": (1.8, "valor_pago_ausente_split"),
    "split_payment_transferred_value": (1.8, "valor_repassado_novo_titular"),
    "split_payment_residual_value": (0.0, "valor_residual"),
}


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

    def test_4_sicredi_cnab_240(self):
        """Teste de integração CNAB 240 Sicredi:

        - Validação da preparação dos dados (regras Sicredi)
        - Geração do arquivo de remessa via BRCobranca
        - Processamento do arquivo de retorno e liquidação parcial
        """
        if not self._check_ci_no_brcobranca():
            # Reiniciando a sequencia de Nosso Numero para o teste
            self.own_number_seq_sicredi.number_next = 1
            self._run_invoice_and_order_brcobranca(self.invoice_sicredi_240)

            payment_order = self.invoice_sicredi_240.line_ids.mapped(
                "payment_line_ids"
            ).order_id

            # Manual Sicredi CNAB 240 - item 6.1 (Nomenclatura dos arquivos):
            # Arquivo de remessa no formato CCCCCMDD.XXX, onde:
            # - CCCCC = Código do beneficiário (5 dígitos)
            # - M = Código do mês (1-9 para Jan-Set, O para Out, N para Nov, D para Dez)
            # - DD = Dia da geração
            # - XXX = Extensão/Sequencial
            # (sugestão: 001, 002 ou .REM na integração brcobranca)
            # Teste para validação do nome do arquivo
            file_name = payment_order.get_file_name("240")

            self.assertTrue(file_name.endswith(".REM"))
            self.assertTrue(
                file_name.startswith(
                    payment_order.payment_mode_id.cnab_config_id.cnab_company_bank_code
                )
            )

            # geração do sequencial .RM1; Retorna ex: CCCCCMDD.REM
            base_file_name = payment_order.get_file_name("240")

            # Simula a existência de um arquivo gerado anteriormente no mesmo dia
            self.env["ir.attachment"].create(
                {
                    "name": base_file_name,
                    "res_model": "account.payment.order",
                    "res_id": payment_order.id + 999,
                    "datas": False,
                }
            )

            # Chama novamente o método para validar a alteração da extensão para .RM1
            second_file_name = payment_order._get_file_name_748(
                "240", fields.Date.context_today(payment_order)
            )
            self.assertTrue(
                second_file_name.endswith(".RM1"),
                "Quando já existir um arquivo gerado no dia, a extensão deve ser .RM1",
            )

            bank_account_id = payment_order.journal_id.bank_account_id
            bank_brcobranca = get_brcobranca_bank(bank_account_id, "240")

            for line in payment_order.payment_line_ids:
                prepared = line.prepare_bank_payment_line(bank_brcobranca)
                cnab_config = line.order_id.payment_mode_id.cnab_config_id

                sequencial = "".join(
                    ch for ch in str(line.own_number) if ch.isdigit()
                ).zfill(5)[-5:]

                ano = self.invoice_sicredi_240.invoice_date.strftime("%y")
                nosso_numero_with_byte_idt = (
                    ano + cnab_config.boleto_byte_idt + sequencial
                )

                nosso_numero_para_calcular_dv = (
                    bank_account_id.bra_number
                    + cnab_config.boleto_post.zfill(2)
                    + cnab_config.cnab_company_bank_code
                    + nosso_numero_with_byte_idt
                )
                expected_nosso_numero = nosso_numero_with_byte_idt + str(
                    modulo11(nosso_numero_para_calcular_dv, 9, 0)
                )

                # Asserções de regras específicas do Sicredi Nosso Numero
                self.assertEqual(prepared["nosso_numero"], expected_nosso_numero)

            payment_file, filename = payment_order.generate_payment_file()
            payment_file_content = payment_file.decode("utf-8")

            # Valida presença dos Nossos Números formatados no texto do arquivo
            self.assertIn("262000017", payment_file_content)
            self.assertIn("262000025", payment_file_content)

            # Importa retorno e valida efeito contábil
            moves = self._run_import_return_file(
                "CNAB240SICREDIRET.RET",
                self.journal_sicredi,
            )

            self.assertEqual(self.invoice_sicredi_240.payment_state, "partial")
            self.assertEqual(moves.date.strftime("%Y-%m-%d"), "2026-08-12")

            # --- Validações da regra: valor_recebido_calculado == 0 ---

            # Conta a Receber associada
            receivable_account = self.invoice_sicredi_240.line_ids.filtered(
                lambda line: line.account_id.account_type == "asset_receivable"
            ).account_id

            all_move_lines = moves.line_ids

            # 1. Testa (valor_recebido_calculado > 0 -> CRIA a linha de crédito)
            liquidation_line_paid = all_move_lines.filtered(
                lambda line: line.account_id == receivable_account
                and line.cnab_returned_ref == "1"
            )
            self.assertTrue(
                liquidation_line_paid,
                "Para valor_recebido_calculado > 0,"
                " a linha de liquidação DEVE ser criada.",
            )
            self.assertEqual(round(liquidation_line_paid.credit, 2), 805.00)

            # 2. Testa (valor_recebido_calculado == 0 -> NÃO CRIA a linha de crédito)
            liquidation_line_0_val = all_move_lines.filtered(
                lambda line: line.account_id == receivable_account
                and line.cnab_returned_ref == "2"
            )
            self.assertFalse(
                liquidation_line_0_val,
                "Para valor_recebido_calculado == 0,"
                " a linha de liquidação NÃO deve ser criada.",
            )

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

    def test_6_return_file_duplicated_own_number(self):
        """
        Test import Return File with the same Own Number/Nosso Número in more
        than one account.move.line of the journal, case that happens when the
        sequence is restarted/recreated, when more than one Payment Mode uses
        the same journal or in migrated data.
        """
        # Título antigo, de mesmo Nosso Número, já liquidado
        invoice_paid = self.invoice_santander_240.copy()
        invoice_paid.action_post()
        self._make_payment(invoice_paid, invoice_paid.amount_residual)
        self.assertTrue(all(invoice_paid.due_line_ids.mapped("reconciled")))

        invoice = self.invoice_santander_240
        invoice.action_post()
        move_line = invoice.due_line_ids[0]
        # As duas parcelas em aberto e a já liquidada com o mesmo Nosso Número
        (invoice.due_line_ids | invoice_paid.due_line_ids[0]).write(
            {"own_number": "40576"}
        )

        # No arquivo de retorno o Nosso Número vem com o Dígito Verificador
        linha_cnab = {
            "codigo_registro": "3",
            "codigo_ocorrencia": "02",
            "nosso_numero": "0000000405760",
            "documento_numero": move_line.document_number,
            "valor_titulo": "000000000150000",
            "data_vencimento": "13102026",
            "data_ocorrencia": "09102026",
        }
        # Antes da correção o processo quebrava com "Expected singleton"
        parser = CNABFileParser(self.journal_santander_240)
        parser.process_return_file([linha_cnab])

        # O título encontrado deve ser o que está em Aberto e não o liquidado
        self.assertEqual(len(parser.cnab_return_events), 1)
        self.assertEqual(parser.cnab_return_events[0]["move_line_id"], move_line.id)
        self.assertEqual(move_line.cnab_state, "accepted")

    def test_brcobranca_error_message(self):
        """Mensagem de erro da API que o usuário vê ao enviar a Remessa.

        A API responde as recusas de payload em JSON, com o texto para o
        usuário na chave `erro` (a frase nomeia o BRCobranca, que é quem não
        conhece o campo recebido), e as demais falhas voltam em texto, que é o
        que vale, veja https://github.com/OCA/l10n-brazil/issues/5146 .
        """

        class FakeResponse:
            def __init__(self, text, json_body=None):
                self.text = text
                self.json_body = json_body

            def json(self):
                if self.json_body is None:
                    raise ValueError("Response body is not JSON.")
                return self.json_body

        payment_order = self.env["account.payment.order"]

        # Recusa de chave desconhecida: o texto para o usuário está em `erro`
        self.assertEqual(
            payment_order._get_brcobranca_error_message(
                FakeResponse(
                    '{"campos_desconhecidos": ["l10n_br_document_key"], "erro": '
                    '"Campos desconhecidos no BRCobranca: l10n_br_document_key"}',
                    {
                        "campos_desconhecidos": ["l10n_br_document_key"],
                        "erro": "Campos desconhecidos no BRCobranca: "
                        "l10n_br_document_key",
                    },
                )
            ),
            "Campos desconhecidos no BRCobranca: l10n_br_document_key",
        )

        # Corpo em texto (validação do BRCobranca): volta como veio
        self.assertEqual(
            payment_order._get_brcobranca_error_message(
                FakeResponse("Registro rejeitado pelo BRCobranca")
            ),
            "Registro rejeitado pelo BRCobranca",
        )

        # JSON sem a chave `erro`: o corpo original é o que sobra
        self.assertEqual(
            payment_order._get_brcobranca_error_message(
                FakeResponse('["Registro rejeitado"]', ["Registro rejeitado"])
            ),
            '["Registro rejeitado"]',
        )

    def test_split_payment(self):
        """Contrato do Split Payment do IBS/CBS (LC 214/2025) com o BRCobranca.

        O que é do módulo comum não é testado aqui: o dicionário do Boleto
        montado pelo `_prepare_boleto_line_vals` (com os atributos
        `documento_fiscal`, `valor_ibs` e `valor_cbs`) e quando informar são
        cobertos no l10n_br_account_payment_order, veja
        `test_payment_line_split_payment_boleto_vals`. Aqui ficam as duas coisas
        que são do processador, veja
        https://github.com/OCA/l10n-brazil/issues/5146 :

        1. o contrato do dicionário com a API, que não aceita os nomes dos
           campos do Odoo: o BRCobranca faz send "#{campo}=" em cada chave e
           uma chave desconhecida gera NoMethodError, então a API recusa o
           payload com HTTP 400 e a mensagem "Campos desconhecidos no
           payload: <chaves>";
        2. o mapeamento dos Segmentos X-03 (dados fiscais e CBS/IBS) e X-04
           (valores da liquidação) do Retorno no Evento do Retorno
           (l10n_br_cnab.return.event).

        A Configuração CNAB usada é a da CAIXA 240, que tem os Códigos de
        Movimento da Entrada e da Alteração do Valor do Título. O caminho de
        ponta a ponta (remessa/retorno na API) é o
        test_split_payment_ailos_cnab_240.
        """
        # 1) Contrato do dicionário do Boleto com a API: com o Split Payment
        # informado, as chaves têm de ser as do BRCobranca e não as do Odoo,
        # que a API recusa com HTTP 400
        self._invoice_confirm_workflow(self.invoice_cef_240)
        payment_order = self._get_draft_payment_order(self.invoice_cef_240)
        line = payment_order.payment_line_ids[0]
        cnab_config = payment_order.payment_mode_id.cnab_config_id
        # A linha criada ao confirmar a fatura está na Entrada de Títulos, um
        # dos eventos em que o Segmento X-03 é previsto
        self.assertEqual(line.instruction_move_code_id, cnab_config.sending_code_id)
        line.date = fields.Date.today()
        cnab_config.use_split_payment = True
        line.write(
            {
                "l10n_br_document_key": SPLIT_PAYMENT_DOCUMENT_KEY,
                "l10n_br_ibs_value": 0.2,
                "l10n_br_cbs_value": 1.8,
            }
        )
        # O dicionário do Boleto é montado no módulo comum
        # (l10n_br_account_payment_order) e já sai com os atributos do
        # BRCobranca que geram o Segmento X-03, o processador não tem o que
        # acrescentar aqui: o que se verifica neste módulo é só o contrato
        # abaixo.
        self.assertFalse(
            {"l10n_br_document_key", "l10n_br_ibs_value", "l10n_br_cbs_value"}
            & set(line._prepare_boleto_line_vals())
        )

        # 2) Mapeamento dos Segmentos X-03/X-04 no Evento do Retorno, com os
        # valores crus do arquivo (15 posições, as 2 últimas decimais)
        parser = CNABFileParser(self.journal_ailos)
        # Arquivo sem os Segmentos X-03/X-04: nenhum campo entra no Evento
        self.assertFalse(parser._get_split_payment_event_vals({"nosso_numero": "1"}))
        from_file = {
            brcobranca_key: f"{value * 100:015.0f}"
            if isinstance(value, float)
            else value
            for value, brcobranca_key in SPLIT_PAYMENT_EVENT_VALUES.values()
        }
        self.assertEqual(
            parser._get_split_payment_event_vals(from_file),
            {
                event_field: value
                for event_field, (value, _) in SPLIT_PAYMENT_EVENT_VALUES.items()
            },
        )

    def test_split_payment_ailos_cnab_240(self):
        """Remessa e Retorno CNAB 240 do AILOS com o Split Payment IBS/CBS.

        A remessa sai com o Segmento X-03 nas posições do Layout Padrão Febraban
        240 posições V11.0 e com os trailers contando o registro; o retorno
        CNAB240AILOS_SPLIT_PAYMENT.RET traz os Segmentos X-03/X-04 em apenas um
        dos títulos (o outro fica vazio) e a fatura fica conciliada, veja
        https://github.com/OCA/l10n-brazil/issues/5146 . Só uma das linhas de
        pagamento informa os dados: o tributo é do título e não pode vazar para
        o outro (o rateio entre as parcelas é testado no
        l10n_br_account_payment_order). O contrato das duas pontas, sem a API, é
        o test_split_payment.
        """
        if not self._check_ci_no_brcobranca():
            # Reiniciando a sequencia de Nosso Numero para casar com os Nosso
            # Numeros do arquivo de retorno (a sequencia não é revertida junto
            # com a transação do teste, mesmo procedimento do teste do Sicredi)
            self.own_number_seq_ailos.number_next = 1
            self._invoice_confirm_workflow(self.invoice_ailos_240)
            payment_order = self._get_draft_payment_order(self.invoice_ailos_240)
            payment_lines = payment_order.payment_line_ids
            self.assertEqual(len(payment_lines), 2)
            payment_order.payment_mode_id.cnab_config_id.use_split_payment = True
            payment_lines[0].write(
                {
                    "l10n_br_document_key": SPLIT_PAYMENT_DOCUMENT_KEY,
                    "l10n_br_ibs_value": 0.2,
                    "l10n_br_cbs_value": 1.8,
                }
            )
            self._run_payment_order_workflow(payment_order, test_not_create_file=False)

            # Remessa: o Segmento X-03 do título que tem os dados
            attachment = self.env["ir.attachment"].search(
                [
                    ("res_model", "=", "account.payment.order"),
                    ("res_id", "=", payment_order.id),
                ],
                order="id desc",
                limit=1,
            )
            self.assertTrue(attachment, "Payment file attachment not created.")
            content = base64.b64decode(attachment.datas).decode()
            lines = [line for line in content.replace("\r", "").split("\n") if line]
            # CNAB é formato de posição fixa: uma linha com 241 quebra o arquivo
            self.assertEqual({len(line) for line in lines}, {240})
            # Segmento X-03: 'X' na posição 14 e identificação 03 nas 16-17
            x03_lines = [
                line for line in lines if line[13] == "X" and line[15:17] == "03"
            ]
            self.assertEqual(len(x03_lines), 1)
            x03_line = x03_lines[0]
            # CBS/IBS Informado no padrão 13 dígitos inteiros e 2 decimais
            self.assertEqual(
                (x03_line[17:67].strip(), x03_line[67:82], x03_line[82:97]),
                (SPLIT_PAYMENT_DOCUMENT_KEY, "000000000000180", "000000000000020"),
            )
            # Do X104 em diante é preenchido pelo Banco no retorno
            self.assertFalse(x03_line[97:].strip())
            # Os trailers contam o registro a mais (o AILOS sobrescreve o
            # total_segmentos por causa do Segmento R opcional)
            batch_trailer = [line for line in lines if line[7] == "5"][0]
            file_trailer = [line for line in lines if line[7] == "9"][0]
            detail_lines = [line for line in lines if line[7] == "3"]
            self.assertEqual(int(batch_trailer[17:23]), len(detail_lines) + 2)
            self.assertEqual(int(file_trailer[23:29]), len(lines))

            # Retorno: os Segmentos X-03/X-04 chegam no Evento do título
            moves = self._run_import_return_file(
                "CNAB240AILOS_SPLIT_PAYMENT.RET",
                self.journal_ailos,
            )
            events = moves.cnab_return_log_id.event_ids
            self.assertEqual(len(events), 2)
            split_event = events.filtered(lambda e: e.own_number == "1")
            self.assertEqual(len(split_event), 1)
            expected = {
                event_field: value
                for event_field, (value, _) in SPLIT_PAYMENT_EVENT_VALUES.items()
            }
            self.assertEqual(
                {event_field: split_event[event_field] for event_field in expected},
                expected,
            )
            # O título sem os registros não herda os dados do anterior
            event_without_split = events.filtered(lambda e: e.own_number == "2")
            self.assertEqual(len(event_without_split), 1)
            self.assertFalse(
                [
                    event_field
                    for event_field in expected
                    if event_without_split[event_field]
                ]
            )

            # Conciliação da fatura: os dois títulos foram liquidados pelo
            # retorno e não sobra saldo a receber
            self.assertEqual(self.invoice_ailos_240.payment_state, "paid")
            installments = self.invoice_ailos_240.line_ids.filtered(
                lambda line: line.account_id.account_type == "asset_receivable"
            )
            self.assertEqual(len(installments), 2)
            self.assertTrue(all(installments.mapped("reconciled")))
            self.assertEqual(sum(installments.mapped("amount_residual")), 0.0)
