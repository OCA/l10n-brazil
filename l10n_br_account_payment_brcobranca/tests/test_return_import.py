# Copyright 2021 Akretion - Raphaël Valyi <raphael.valyi@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)
# Copyright (C) 2021-Today - Akretion (<http://www.akretion.com>).
# @author Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
import datetime
import os
from unittest import mock

from odoo.modules import get_resource_path
from odoo.tests import SavepointCase, tagged

_module_ns = "odoo.addons.l10n_br_account_payment_brcobranca"
_provider_class_pay_order = (
    _module_ns + ".models.account_payment_order" + ".PaymentOrder"
)
_provider_class = _module_ns + ".parser.cnab_file_parser" + ".CNABFileParser"


@tagged("post_install", "-at_install")
class TestReturnImport(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company_a = cls.env.ref("base.main_company")
        cls.account_move_obj = cls.env["account.move"]
        cls.account_move_line_obj = cls.env["account.move.line"]
        cls.cnab_log_obj = cls.env["l10n_br_cnab.return.log"]

        cls.account_id = cls.env.ref(
            "l10n_br_account_payment_order.1_account_template_3010101010200_avoid_travis_error"
        )
        cls.bank_account = cls.env["account.account"].create(
            {
                "code": "X1014",
                "name": "Bank Current Account - (test)",
                "user_type_id": cls.env.ref("account.data_account_type_liquidity").id,
            }
        )
        cls.import_wizard_obj = cls.env["credit.statement.import"]

        # Get Invoice for test
        cls.invoice_unicred_1 = cls.env.ref(
            "l10n_br_account_payment_order."
            "demo_invoice_payment_order_unicred_cnab400"
        )
        cls.invoice_unicred_2 = cls.env.ref(
            "l10n_br_account_payment_brcobranca."
            "demo_invoice_brcobranca_unicred_cnab400"
        )

        cls.invoice_ailos_1 = cls.env.ref(
            "l10n_br_account_payment_order." "demo_invoice_payment_order_ailos_cnab240"
        )
        cls.invoice_bancobrasil_1 = cls.env.ref(
            "l10n_br_account_payment_order." "demo_invoice_payment_order_bb_cnab400"
        )

        cls.journal = cls.env.ref("l10n_br_account_payment_order.unicred_journal")

        # I validate invoice by creating on
        cls.invoice_unicred_1.action_post()
        cls.invoice_unicred_2.action_post()
        cls.invoice_ailos_1.action_post()
        cls.invoice_bancobrasil_1.action_post()

        # Para evitar erros nos testes de variação da Sequencia do
        # Nosso Numero/own_number quando se roda mais de uma vez ou
        # devido a diferença entre os comandos feitos pelo Travis
        cls.invoice_unicred_1_own_numbers = []
        for line in cls.invoice_unicred_1.financial_move_line_ids:
            # No arquivo de retorno vem o NOSSO NUMERO + Digito Verificador
            cls.invoice_unicred_1_own_numbers.append(line.own_number + "0")

        cls.invoice_unicred_2_own_numbers = []
        for line in cls.invoice_unicred_2.financial_move_line_ids:
            # No arquivo de retorno vem o NOSSO NUMERO + Digito Verificador
            cls.invoice_unicred_2_own_numbers.append(line.own_number + "0")

        cls.invoice_ailos_1_own_numbers = []
        for line in cls.invoice_ailos_1.financial_move_line_ids:
            cls.invoice_ailos_1_own_numbers.append(line.own_number)

        cls.invoice_bancobrasil_1_own_numbers = []
        for line in cls.invoice_bancobrasil_1.financial_move_line_ids:
            cls.invoice_bancobrasil_1_own_numbers.append(line.own_number)

        payment_order_unicred = cls.env["account.payment.order"].search(
            [("payment_mode_id", "=", cls.invoice_unicred_1.payment_mode_id.id)]
        )

        # Open payment order
        payment_order_unicred.draft2open()

        # Verifica se deve testar com o mock
        if os.environ.get("CI"):
            # Generate
            file_name = get_resource_path(
                "l10n_br_account_payment_brcobranca",
                "tests",
                "data",
                "teste_remessa-unicred_400-1.REM",
            )
            with open(file_name, "rb") as f:
                mocked_response = f.read()
                with mock.patch(
                    _provider_class_pay_order + "._get_brcobranca_remessa",
                    return_value=mocked_response,
                ):
                    payment_order_unicred.open2generated()
        else:
            payment_order_unicred.open2generated()

        # Confirm Upload
        payment_order_unicred.generated2uploaded()

    def _import_file(self, file_name):
        """import a file using the wizard
        return the create account.bank.statement object
        """

        with open(file_name, "rb") as f:
            content = f.read()
            self.wizard = self.import_wizard_obj.create(
                {
                    "journal_id": self.journal.id,
                    "input_statement": base64.b64encode(content),
                    "file_name": os.path.basename(file_name),
                }
            )
            action = self.wizard.import_statement()
            log_view_ref = self.ref(
                "l10n_br_account_payment_order.l10n_br_cnab_return_log_form_view"
            )
            if action["views"] == [(log_view_ref, "form")]:
                return self.cnab_log_obj.browse(action["res_id"])
            else:
                return self.account_move_obj.browse(action["res_id"])

    def _assert_move_entries(self, expected_move_line_values_list, moves_list):
        for expected_move_line_values, move in zip(
            expected_move_line_values_list, moves_list
        ):
            for expected, move_line in zip(expected_move_line_values, move.line_ids):
                self.assertEqual(expected["account_name"], move_line.account_id.name)
                self.assertEqual(expected["debit"], move_line.debit)
                self.assertEqual(expected["credit"], move_line.credit)

    def test_valor_menor_1(self):
        mocked_response = [
            {
                "codigo_registro": "1",
                "codigo_ocorrencia": "02",
                "data_ocorrencia": "210224",
                "agencia_com_dv": None,
                "agencia_sem_dv": "1234",
                "cedente_com_dv": "000003719",
                "convenio": None,
                # "nosso_numero": "00000000000000010",
                "nosso_numero": self.invoice_unicred_1_own_numbers[0],
                "tipo_cobranca": None,
                "tipo_cobranca_anterior": None,
                "natureza_recebimento": None,
                "carteira_variacao": None,
                "desconto": "0000000000300",
                "iof": None,
                "carteira": None,
                "comando": None,
                "data_liquidacao": None,
                "data_vencimento": "060720",
                "valor_titulo": "0000000030000",
                "banco_recebedor": "136",
                "agencia_recebedora_com_dv": "12343",
                "especie_documento": None,
                "data_credito": "060720",
                "valor_tarifa": "0000180",
                "outras_despesas": None,
                "juros_desconto": None,
                "iof_desconto": None,
                "valor_abatimento": "0000000000200",
                "desconto_concedito": None,
                "valor_recebido": "0000000029650",
                "juros_mora": "0000000000000",
                "outros_recebimento": None,
                "abatimento_nao_aproveitado": None,
                "valor_lancamento": None,
                "indicativo_lancamento": None,
                "indicador_valor": None,
                "valor_ajuste": None,
                "sequencial": "00000",
                "arquivo": None,
                "motivo_ocorrencia": [],
                "documento_numero": None,
            },
            {
                "codigo_registro": "1",
                "codigo_ocorrencia": "02",
                "data_ocorrencia": "210224",
                "agencia_com_dv": None,
                "agencia_sem_dv": "1234",
                "cedente_com_dv": "000003719",
                "convenio": None,
                # "nosso_numero": "00000000000000029",
                "nosso_numero": self.invoice_unicred_1_own_numbers[1],
                "tipo_cobranca": None,
                "tipo_cobranca_anterior": None,
                "natureza_recebimento": None,
                "carteira_variacao": None,
                "desconto": "0000000000300",
                "iof": None,
                "carteira": None,
                "comando": None,
                "data_liquidacao": None,
                "data_vencimento": "060720",
                "valor_titulo": "0000000070000",
                "banco_recebedor": "136",
                "agencia_recebedora_com_dv": "12343",
                "especie_documento": None,
                "data_credito": "060720",
                "valor_tarifa": "0000180",
                "outras_despesas": None,
                "juros_desconto": None,
                "iof_desconto": None,
                "valor_abatimento": "0000000000200",
                "desconto_concedito": None,
                "valor_recebido": "0000000069650",
                "juros_mora": "0000000000000",
                "outros_recebimento": None,
                "abatimento_nao_aproveitado": None,
                "valor_lancamento": None,
                "indicativo_lancamento": None,
                "indicador_valor": None,
                "valor_ajuste": None,
                "sequencial": "00000",
                "arquivo": None,
                "motivo_ocorrencia": [],
                "documento_numero": None,
            },
            {
                "codigo_registro": "9",
                "codigo_ocorrencia": "00",
                "data_ocorrencia": "210224",
                "agencia_com_dv": None,
                "agencia_sem_dv": "0000",
                "cedente_com_dv": "000000000",
                "convenio": None,
                "nosso_numero": "00          00000",
                "tipo_cobranca": None,
                "tipo_cobranca_anterior": None,
                "natureza_recebimento": None,
                "carteira_variacao": None,
                "desconto": "0000000",
                "iof": None,
                "carteira": None,
                "comando": None,
                "data_liquidacao": None,
                "data_vencimento": "000000",
                "valor_titulo": "0000000000000",
                "banco_recebedor": "00",
                "agencia_recebedora_com_dv": "",
                "especie_documento": None,
                "data_credito": "000000",
                "valor_tarifa": "",
                "outras_despesas": None,
                "juros_desconto": None,
                "iof_desconto": None,
                "valor_abatimento": "0000000000000",
                "desconto_concedito": None,
                "valor_recebido": "",
                "juros_mora": "",
                "outros_recebimento": None,
                "abatimento_nao_aproveitado": None,
                "valor_lancamento": None,
                "indicativo_lancamento": None,
                "indicador_valor": None,
                "valor_ajuste": None,
                "sequencial": "000016",
                "arquivo": None,
                "motivo_ocorrencia": [],
                "documento_numero": None,
            },
        ]

        with mock.patch(
            _provider_class + "._get_brcobranca_retorno",
            return_value=mocked_response,
        ):
            file_name = get_resource_path(
                "l10n_br_account_payment_brcobranca",
                "tests",
                "data",
                "CNAB400UNICRED_valor_menor_1.RET",
            )
            # Apesar de não haver ocorrências de liquidação,
            # Há ocorrências que geram cobrança de tarifas e
            # Lançamentos contábeis são criados
            # Nesse caso o retorno é um move (lançamento contabil)
            move = self._import_file(file_name)
        self.assertEqual("Banco UNICRED - Conta 371", move.cnab_return_log_id.name)
        self.assertEqual(3.6, move.cnab_return_log_id.amount_total_tariff_charge)
        self.assertEqual(1000.0, move.cnab_return_log_id.amount_total_title)
        self.assertEqual(2, len(move.cnab_return_log_id.move_ids))
        expected_move_line_values_list = [
            [
                {
                    "account_name": "Banco Unicred",
                    "debit": 0.0,
                    "credit": 1.8,
                },
                {
                    "account_name": "Outras Despesas Financeiras - AVOID_TRAVIS_ERROR",
                    "debit": 1.8,
                    "credit": 0.0,
                },
            ],
            [
                {
                    "account_name": "Banco Unicred",
                    "debit": 0.0,
                    "credit": 1.8,
                },
                {
                    "account_name": "Outras Despesas Financeiras - AVOID_TRAVIS_ERROR",
                    "debit": 1.8,
                    "credit": 0.0,
                },
            ],
        ]
        moves = move.cnab_return_log_id.move_ids
        self._assert_move_entries(expected_move_line_values_list, moves)

    def test_valor_menor_2(self):
        mocked_response = [
            {
                "codigo_registro": "1",
                "codigo_ocorrencia": "06",
                "data_ocorrencia": "210224",
                "agencia_com_dv": None,
                "agencia_sem_dv": "1234",
                "cedente_com_dv": "000003719",
                "convenio": None,
                # "nosso_numero": "00000000000000090",
                "nosso_numero": self.invoice_unicred_1_own_numbers[0],
                "tipo_cobranca": None,
                "tipo_cobranca_anterior": None,
                "natureza_recebimento": None,
                "carteira_variacao": None,
                "desconto": "0000000000300",
                "iof": None,
                "carteira": None,
                "comando": None,
                "data_liquidacao": None,
                "data_vencimento": "060720",
                "valor_titulo": "0000000030000",
                "banco_recebedor": "136",
                "agencia_recebedora_com_dv": "12343",
                "especie_documento": None,
                "data_credito": "060720",
                "valor_tarifa": "0000180",
                "outras_despesas": None,
                "juros_desconto": None,
                "iof_desconto": None,
                "valor_abatimento": "0000000000200",
                "desconto_concedito": None,
                "valor_recebido": "0000000029500",
                "juros_mora": "0000000000000",
                "outros_recebimento": None,
                "abatimento_nao_aproveitado": None,
                "valor_lancamento": None,
                "indicativo_lancamento": None,
                "indicador_valor": None,
                "valor_ajuste": None,
                "sequencial": "00000",
                "arquivo": None,
                "motivo_ocorrencia": [],
                "documento_numero": None,
            },
            {
                "codigo_registro": "1",
                "codigo_ocorrencia": "06",
                "data_ocorrencia": "210224",
                "agencia_com_dv": None,
                "agencia_sem_dv": "1234",
                "cedente_com_dv": "000003719",
                "convenio": None,
                # "nosso_numero": "00000000000000109",
                "nosso_numero": self.invoice_unicred_1_own_numbers[1],
                "tipo_cobranca": None,
                "tipo_cobranca_anterior": None,
                "natureza_recebimento": None,
                "carteira_variacao": None,
                "desconto": "0000000000300",
                "iof": None,
                "carteira": None,
                "comando": None,
                "data_liquidacao": None,
                "data_vencimento": "060720",
                "valor_titulo": "0000000070000",
                "banco_recebedor": "136",
                "agencia_recebedora_com_dv": "12343",
                "especie_documento": None,
                "data_credito": "060720",
                "valor_tarifa": "0000180",
                "outras_despesas": None,
                "juros_desconto": None,
                "iof_desconto": None,
                "valor_abatimento": "0000000000200",
                "desconto_concedito": None,
                "valor_recebido": "0000000069500",
                "juros_mora": "0000000000000",
                "outros_recebimento": None,
                "abatimento_nao_aproveitado": None,
                "valor_lancamento": None,
                "indicativo_lancamento": None,
                "indicador_valor": None,
                "valor_ajuste": None,
                "sequencial": "00000",
                "arquivo": None,
                "motivo_ocorrencia": [],
                "documento_numero": None,
            },
            {
                "codigo_registro": "9",
                "codigo_ocorrencia": "00",
                "data_ocorrencia": "210224",
                "agencia_com_dv": None,
                "agencia_sem_dv": "0000",
                "cedente_com_dv": "000000000",
                "convenio": None,
                "nosso_numero": "00          00000",
                "tipo_cobranca": None,
                "tipo_cobranca_anterior": None,
                "natureza_recebimento": None,
                "carteira_variacao": None,
                "desconto": "0000000",
                "iof": None,
                "carteira": None,
                "comando": None,
                "data_liquidacao": None,
                "data_vencimento": "000000",
                "valor_titulo": "0000000000000",
                "banco_recebedor": "00",
                "agencia_recebedora_com_dv": "",
                "especie_documento": None,
                "data_credito": "000000",
                "valor_tarifa": "",
                "outras_despesas": None,
                "juros_desconto": None,
                "iof_desconto": None,
                "valor_abatimento": "0000000000000",
                "desconto_concedito": None,
                "valor_recebido": "",
                "juros_mora": "",
                "outros_recebimento": None,
                "abatimento_nao_aproveitado": None,
                "valor_lancamento": None,
                "indicativo_lancamento": None,
                "indicador_valor": None,
                "valor_ajuste": None,
                "sequencial": "000016",
                "arquivo": None,
                "motivo_ocorrencia": [],
                "documento_numero": None,
            },
        ]

        with mock.patch(
            _provider_class + "._get_brcobranca_retorno",
            return_value=mocked_response,
        ):
            file_name = get_resource_path(
                "l10n_br_account_payment_brcobranca",
                "tests",
                "data",
                "CNAB400UNICRED_valor_menor_2.RET",
            )
            # Retorna o primeiro account.move criado.
            move = self._import_file(file_name)

        self.assertEqual("Retorno CNAB - Banco UNICRED - Conta 371", move.ref)
        # I check that the invoice state is "Paid"
        self.assertEqual(self.invoice_unicred_1.payment_state, "paid")
        self.assertEqual(2, len(move.cnab_return_log_id.move_ids))
        self.assertEqual(3.6, move.cnab_return_log_id.amount_total_tariff_charge)
        self.assertEqual(1000.0, move.cnab_return_log_id.amount_total_title)
        expected_move_line_values_list = [
            [
                {
                    "account_name": "Despesas com Vendas - AVOID_TRAVIS_ERROR",
                    "debit": 3.0,
                    "credit": 0.0,
                },
                {
                    "account_name": "Banco Unicred",
                    "debit": 0.0,
                    "credit": 3.0,
                },
                {
                    "account_name": "Outras Despesas Gerais - AVOID_TRAVIS_ERROR",
                    "debit": 2.0,
                    "credit": 0.0,
                },
                {
                    "account_name": "Banco Unicred",
                    "debit": 0.0,
                    "credit": 2.0,
                },
                {
                    "account_name": "Account Receivable",
                    "debit": 0.0,
                    "credit": 300.0,
                },
                {
                    "account_name": "Banco Unicred",
                    "debit": 0.0,
                    "credit": 1.8,
                },
                {
                    "account_name": "Outras Despesas Financeiras - AVOID_TRAVIS_ERROR",
                    "debit": 1.8,
                    "credit": 0.0,
                },
                {
                    "account_name": "Banco Unicred",
                    "debit": 300.0,
                    "credit": 0.0,
                },
            ],
            [
                {
                    "account_name": "Despesas com Vendas - AVOID_TRAVIS_ERROR",
                    "debit": 3.0,
                    "credit": 0.0,
                },
                {
                    "account_name": "Banco Unicred",
                    "debit": 0.0,
                    "credit": 3.0,
                },
                {
                    "account_name": "Outras Despesas Gerais - AVOID_TRAVIS_ERROR",
                    "debit": 2.0,
                    "credit": 0.0,
                },
                {
                    "account_name": "Banco Unicred",
                    "debit": 0.0,
                    "credit": 2.0,
                },
                {
                    "account_name": "Account Receivable",
                    "debit": 0.0,
                    "credit": 700.0,
                },
                {
                    "account_name": "Banco Unicred",
                    "debit": 0.0,
                    "credit": 1.8,
                },
                {
                    "account_name": "Outras Despesas Financeiras - AVOID_TRAVIS_ERROR",
                    "debit": 1.8,
                    "credit": 0.0,
                },
                {
                    "account_name": "Banco Unicred",
                    "debit": 700.0,
                    "credit": 0.0,
                },
            ],
        ]
        moves = move.cnab_return_log_id.move_ids
        self._assert_move_entries(expected_move_line_values_list, moves)

    def test_valor_maior_3(self):
        mocked_response = [
            {
                "codigo_registro": "1",
                "codigo_ocorrencia": "02",
                "data_ocorrencia": "210224",
                "agencia_com_dv": None,
                "agencia_sem_dv": "1234",
                "cedente_com_dv": "000003719",
                "convenio": None,
                # "nosso_numero": "00000000000000030",
                "nosso_numero": self.invoice_unicred_2_own_numbers[0],
                "tipo_cobranca": None,
                "tipo_cobranca_anterior": None,
                "natureza_recebimento": None,
                "carteira_variacao": None,
                "desconto": "0000000000000",
                "iof": None,
                "carteira": None,
                "comando": None,
                "data_liquidacao": None,
                "data_vencimento": "060720",
                "valor_titulo": "0000000030000",
                "banco_recebedor": "136",
                "agencia_recebedora_com_dv": "12343",
                "especie_documento": None,
                "data_credito": "060720",
                "valor_tarifa": "0000180",
                "outras_despesas": None,
                "juros_desconto": None,
                "iof_desconto": None,
                "valor_abatimento": "0000000000000",
                "desconto_concedito": None,
                "valor_recebido": "0000000031000",
                "juros_mora": "0000000001000",
                "outros_recebimento": None,
                "abatimento_nao_aproveitado": None,
                "valor_lancamento": None,
                "indicativo_lancamento": None,
                "indicador_valor": None,
                "valor_ajuste": None,
                "sequencial": "00000",
                "arquivo": None,
                "motivo_ocorrencia": [],
                "documento_numero": None,
            },
            {
                "codigo_registro": "1",
                "codigo_ocorrencia": "02",
                "data_ocorrencia": "210224",
                "agencia_com_dv": None,
                "agencia_sem_dv": "1234",
                "cedente_com_dv": "000003719",
                "convenio": None,
                # "nosso_numero": "00000000000000049",
                "nosso_numero": self.invoice_unicred_2_own_numbers[1],
                "tipo_cobranca": None,
                "tipo_cobranca_anterior": None,
                "natureza_recebimento": None,
                "carteira_variacao": None,
                "desconto": "0000000000000",
                "iof": None,
                "carteira": None,
                "comando": None,
                "data_liquidacao": None,
                "data_vencimento": "060720",
                "valor_titulo": "0000000070000",
                "banco_recebedor": "136",
                "agencia_recebedora_com_dv": "12343",
                "especie_documento": None,
                "data_credito": "060720",
                "valor_tarifa": "0000180",
                "outras_despesas": None,
                "juros_desconto": None,
                "iof_desconto": None,
                "valor_abatimento": "0000000000000",
                "desconto_concedito": None,
                "valor_recebido": "0000000071000",
                "juros_mora": "0000000001000",
                "outros_recebimento": None,
                "abatimento_nao_aproveitado": None,
                "valor_lancamento": None,
                "indicativo_lancamento": None,
                "indicador_valor": None,
                "valor_ajuste": None,
                "sequencial": "00000",
                "arquivo": None,
                "motivo_ocorrencia": [],
                "documento_numero": None,
            },
            {
                "codigo_registro": "9",
                "codigo_ocorrencia": "00",
                "data_ocorrencia": "210224",
                "agencia_com_dv": None,
                "agencia_sem_dv": "0000",
                "cedente_com_dv": "000000000",
                "convenio": None,
                "nosso_numero": "00          00000",
                "tipo_cobranca": None,
                "tipo_cobranca_anterior": None,
                "natureza_recebimento": None,
                "carteira_variacao": None,
                "desconto": "0000000",
                "iof": None,
                "carteira": None,
                "comando": None,
                "data_liquidacao": None,
                "data_vencimento": "000000",
                "valor_titulo": "0000000000000",
                "banco_recebedor": "00",
                "agencia_recebedora_com_dv": "",
                "especie_documento": None,
                "data_credito": "000000",
                "valor_tarifa": "",
                "outras_despesas": None,
                "juros_desconto": None,
                "iof_desconto": None,
                "valor_abatimento": "0000000000000",
                "desconto_concedito": None,
                "valor_recebido": "",
                "juros_mora": "",
                "outros_recebimento": None,
                "abatimento_nao_aproveitado": None,
                "valor_lancamento": None,
                "indicativo_lancamento": None,
                "indicador_valor": None,
                "valor_ajuste": None,
                "sequencial": "000016",
                "arquivo": None,
                "motivo_ocorrencia": [],
                "documento_numero": None,
            },
        ]

        with mock.patch(
            _provider_class + "._get_brcobranca_retorno",
            return_value=mocked_response,
        ):
            file_name = get_resource_path(
                "l10n_br_account_payment_brcobranca",
                "tests",
                "data",
                "CNAB400UNICRED_valor_maior_3.RET",
            )
            # Apesar de não haver ocorrências de liquidação,
            # Há ocorrências que geram cobrança de tarifas e
            # Lançamentos contábeis são criados
            # Nesse caso o retorno é um move (lançamento contabil)
            move = self._import_file(file_name)

        self.assertEqual("Banco UNICRED - Conta 371", move.cnab_return_log_id.name)
        self.assertEqual(2, len(move.cnab_return_log_id.move_ids))
        self.assertEqual(3.6, move.cnab_return_log_id.amount_total_tariff_charge)
        self.assertEqual(1000.0, move.cnab_return_log_id.amount_total_title)
        expected_move_line_values_list = [
            [
                {
                    "account_name": "Banco Unicred",
                    "debit": 0.0,
                    "credit": 1.8,
                },
                {
                    "account_name": "Outras Despesas Financeiras - AVOID_TRAVIS_ERROR",
                    "debit": 1.8,
                    "credit": 0.0,
                },
            ],
            [
                {
                    "account_name": "Banco Unicred",
                    "debit": 0.0,
                    "credit": 1.8,
                },
                {
                    "account_name": "Outras Despesas Financeiras - AVOID_TRAVIS_ERROR",
                    "debit": 1.8,
                    "credit": 0.0,
                },
            ],
        ]
        moves = move.cnab_return_log_id.move_ids
        self._assert_move_entries(expected_move_line_values_list, moves)

    def test_valor_maior_4(self):
        mocked_response = [
            {
                "codigo_registro": "1",
                "codigo_ocorrencia": "06",
                "data_ocorrencia": "210224",
                "agencia_com_dv": None,
                "agencia_sem_dv": "1234",
                "cedente_com_dv": "000003719",
                "convenio": None,
                # "nosso_numero": "00000000000000110",
                "nosso_numero": self.invoice_unicred_2_own_numbers[0],
                "tipo_cobranca": None,
                "tipo_cobranca_anterior": None,
                "natureza_recebimento": None,
                "carteira_variacao": None,
                "desconto": "0000000000000",
                "iof": None,
                "carteira": None,
                "comando": None,
                "data_liquidacao": None,
                "data_vencimento": "060720",
                "valor_titulo": "0000000030000",
                "banco_recebedor": "136",
                "agencia_recebedora_com_dv": "12343",
                "especie_documento": None,
                "data_credito": "060720",
                "valor_tarifa": "0000180",
                "outras_despesas": None,
                "juros_desconto": None,
                "iof_desconto": None,
                "valor_abatimento": "0000000000000",
                "desconto_concedito": None,
                "valor_recebido": "0000000031000",
                "juros_mora": "0000000001000",
                "outros_recebimento": None,
                "abatimento_nao_aproveitado": None,
                "valor_lancamento": None,
                "indicativo_lancamento": None,
                "indicador_valor": None,
                "valor_ajuste": None,
                "sequencial": "00000",
                "arquivo": None,
                "motivo_ocorrencia": [],
                "documento_numero": None,
            },
            {
                "codigo_registro": "1",
                "codigo_ocorrencia": "06",
                "data_ocorrencia": "210224",
                "agencia_com_dv": None,
                "agencia_sem_dv": "1234",
                "cedente_com_dv": "000003719",
                "convenio": None,
                # "nosso_numero": "00000000000000129",
                "nosso_numero": self.invoice_unicred_2_own_numbers[1],
                "tipo_cobranca": None,
                "tipo_cobranca_anterior": None,
                "natureza_recebimento": None,
                "carteira_variacao": None,
                "desconto": "0000000000000",
                "iof": None,
                "carteira": None,
                "comando": None,
                "data_liquidacao": None,
                "data_vencimento": "060720",
                "valor_titulo": "0000000070000",
                "banco_recebedor": "136",
                "agencia_recebedora_com_dv": "12343",
                "especie_documento": None,
                "data_credito": "060720",
                "valor_tarifa": "0000180",
                "outras_despesas": None,
                "juros_desconto": None,
                "iof_desconto": None,
                "valor_abatimento": "0000000000000",
                "desconto_concedito": None,
                "valor_recebido": "0000000071000",
                "juros_mora": "0000000001000",
                "outros_recebimento": None,
                "abatimento_nao_aproveitado": None,
                "valor_lancamento": None,
                "indicativo_lancamento": None,
                "indicador_valor": None,
                "valor_ajuste": None,
                "sequencial": "00000",
                "arquivo": None,
                "motivo_ocorrencia": [],
                "documento_numero": None,
            },
            {
                "codigo_registro": "9",
                "codigo_ocorrencia": "00",
                "data_ocorrencia": "210224",
                "agencia_com_dv": None,
                "agencia_sem_dv": "0000",
                "cedente_com_dv": "000000000",
                "convenio": None,
                "nosso_numero": "00          00000",
                "tipo_cobranca": None,
                "tipo_cobranca_anterior": None,
                "natureza_recebimento": None,
                "carteira_variacao": None,
                "desconto": "0000000",
                "iof": None,
                "carteira": None,
                "comando": None,
                "data_liquidacao": None,
                "data_vencimento": "000000",
                "valor_titulo": "0000000000000",
                "banco_recebedor": "00",
                "agencia_recebedora_com_dv": "",
                "especie_documento": None,
                "data_credito": "000000",
                "valor_tarifa": "",
                "outras_despesas": None,
                "juros_desconto": None,
                "iof_desconto": None,
                "valor_abatimento": "0000000000000",
                "desconto_concedito": None,
                "valor_recebido": "",
                "juros_mora": "",
                "outros_recebimento": None,
                "abatimento_nao_aproveitado": None,
                "valor_lancamento": None,
                "indicativo_lancamento": None,
                "indicador_valor": None,
                "valor_ajuste": None,
                "sequencial": "000016",
                "arquivo": None,
                "motivo_ocorrencia": [],
                "documento_numero": None,
            },
        ]

        with mock.patch(
            _provider_class + "._get_brcobranca_retorno",
            return_value=mocked_response,
        ):
            file_name = get_resource_path(
                "l10n_br_account_payment_brcobranca",
                "tests",
                "data",
                "CNAB400UNICRED_valor_maior_4.RET",
            )
            # Retorna o primeiro account.move criado.
            move = self._import_file(file_name)

        self.assertEqual("Retorno CNAB - Banco UNICRED - Conta 371", move.ref)
        # I check that the invoice state is "Paid"
        self.assertEqual(self.invoice_unicred_2.payment_state, "paid")
        self.assertEqual(2, len(move.cnab_return_log_id.move_ids))
        self.assertEqual(3.6, move.cnab_return_log_id.amount_total_tariff_charge)
        self.assertEqual(1000.0, move.cnab_return_log_id.amount_total_title)
        expected_move_line_values_list = [
            [
                {
                    "account_name": "Juros Ativos - AVOID_TRAVIS_ERROR",
                    "debit": 0.0,
                    "credit": 10.0,
                },
                {
                    "account_name": "Banco Unicred",
                    "debit": 10.0,
                    "credit": 0.0,
                },
                {
                    "account_name": "Account Receivable",
                    "debit": 0.0,
                    "credit": 300.0,
                },
                {
                    "account_name": "Banco Unicred",
                    "debit": 0.0,
                    "credit": 1.8,
                },
                {
                    "account_name": "Outras Despesas Financeiras - AVOID_TRAVIS_ERROR",
                    "debit": 1.8,
                    "credit": 0.0,
                },
                {
                    "account_name": "Banco Unicred",
                    "debit": 300.0,
                    "credit": 0.0,
                },
            ],
            [
                {
                    "account_name": "Juros Ativos - AVOID_TRAVIS_ERROR",
                    "debit": 0.0,
                    "credit": 10.0,
                },
                {
                    "account_name": "Banco Unicred",
                    "debit": 10.0,
                    "credit": 0.0,
                },
                {
                    "account_name": "Account Receivable",
                    "debit": 0.0,
                    "credit": 700.0,
                },
                {
                    "account_name": "Banco Unicred",
                    "debit": 0.0,
                    "credit": 1.8,
                },
                {
                    "account_name": "Outras Despesas Financeiras - AVOID_TRAVIS_ERROR",
                    "debit": 1.8,
                    "credit": 0.0,
                },
                {
                    "account_name": "Banco Unicred",
                    "debit": 700.0,
                    "credit": 0.0,
                },
            ],
        ]
        moves = move.cnab_return_log_id.move_ids
        self._assert_move_entries(expected_move_line_values_list, moves)

    def test_ailos_return(self):
        mocked_response = [
            {
                "codigo_registro": "03",
                "codigo_ocorrencia": "06",
                "data_ocorrencia": "210224",
                "agencia_com_dv": None,
                "agencia_sem_dv": "1234",
                "cedente_com_dv": "000003719",
                "convenio": None,
                "nosso_numero": "00000000000" + self.invoice_ailos_1_own_numbers[0],
                "tipo_cobranca": None,
                "tipo_cobranca_anterior": None,
                "natureza_recebimento": None,
                "carteira_variacao": None,
                "desconto": "0000000000000",
                "iof": None,
                "carteira": None,
                "comando": None,
                "data_liquidacao": None,
                "data_vencimento": "06072021",
                "valor_titulo": "0000000030000",
                "banco_recebedor": "136",
                "agencia_recebedora_com_dv": "12343",
                "especie_documento": None,
                "data_credito": "06072021",
                "valor_tarifa": "0000180",
                "outras_despesas": None,
                "juros_desconto": None,
                "iof_desconto": None,
                "valor_abatimento": "0000000000000",
                "desconto_concedito": None,
                "valor_recebido": "0000000030000",
                "juros_mora": "0000000000000",
                "outros_recebimento": None,
                "abatimento_nao_aproveitado": None,
                "valor_lancamento": None,
                "indicativo_lancamento": None,
                "indicador_valor": None,
                "valor_ajuste": None,
                "sequencial": "00000",
                "arquivo": None,
                "motivo_ocorrencia": [],
                "documento_numero": None,
            },
            {
                "codigo_registro": "03",
                "codigo_ocorrencia": "06",
                "data_ocorrencia": "210224",
                "agencia_com_dv": None,
                "agencia_sem_dv": "1234",
                "cedente_com_dv": "000003719",
                "convenio": None,
                "nosso_numero": "00000000000" + self.invoice_ailos_1_own_numbers[1],
                "tipo_cobranca": None,
                "tipo_cobranca_anterior": None,
                "natureza_recebimento": None,
                "carteira_variacao": None,
                "desconto": "0000000000000",
                "iof": None,
                "carteira": None,
                "comando": None,
                "data_liquidacao": None,
                "data_vencimento": "06072021",
                "valor_titulo": "0000000070000",
                "banco_recebedor": "136",
                "agencia_recebedora_com_dv": "12343",
                "especie_documento": None,
                "data_credito": "06072021",
                "valor_tarifa": "0000180",
                "outras_despesas": None,
                "juros_desconto": None,
                "iof_desconto": None,
                "valor_abatimento": "0000000000000",
                "desconto_concedito": None,
                "valor_recebido": "0000000070000",
                "juros_mora": "0000000000000",
                "outros_recebimento": None,
                "abatimento_nao_aproveitado": None,
                "valor_lancamento": None,
                "indicativo_lancamento": None,
                "indicador_valor": None,
                "valor_ajuste": None,
                "sequencial": "00000",
                "arquivo": None,
                "motivo_ocorrencia": [],
                "documento_numero": None,
            },
            {
                "codigo_registro": "9",
                "codigo_ocorrencia": "00",
                "data_ocorrencia": "210224",
                "agencia_com_dv": None,
                "agencia_sem_dv": "0000",
                "cedente_com_dv": "000000000",
                "convenio": None,
                "nosso_numero": "00          00000",
                "tipo_cobranca": None,
                "tipo_cobranca_anterior": None,
                "natureza_recebimento": None,
                "carteira_variacao": None,
                "desconto": "0000000",
                "iof": None,
                "carteira": None,
                "comando": None,
                "data_liquidacao": None,
                "data_vencimento": "00000000",
                "valor_titulo": "0000000000000",
                "banco_recebedor": "00",
                "agencia_recebedora_com_dv": "",
                "especie_documento": None,
                "data_credito": "00000000",
                "valor_tarifa": "",
                "outras_despesas": None,
                "juros_desconto": None,
                "iof_desconto": None,
                "valor_abatimento": "0000000000000",
                "desconto_concedito": None,
                "valor_recebido": "",
                "juros_mora": "",
                "outros_recebimento": None,
                "abatimento_nao_aproveitado": None,
                "valor_lancamento": None,
                "indicativo_lancamento": None,
                "indicador_valor": None,
                "valor_ajuste": None,
                "sequencial": "000016",
                "arquivo": None,
                "motivo_ocorrencia": [],
                "documento_numero": None,
            },
        ]
        # Verifica se a fatura está aberta, antes de fazer o retorno.
        self.assertEqual(self.invoice_ailos_1.state, "posted")

        self.journal = self.env.ref("l10n_br_account_payment_order.ailos_journal")

        with mock.patch(
            _provider_class + "._get_brcobranca_retorno",
            return_value=mocked_response,
        ):
            file_name = get_resource_path(
                "l10n_br_account_payment_brcobranca",
                "tests",
                "data",
                "CNAB240AILOS.RET",
            )

            # Retorna o primeiro account.move criado.
            move = self._import_file(file_name)

        self.assertEqual(
            "Retorno CNAB - Banco COOP CENTRAL AILOS - Conta 373", move.ref
        )
        # I check that the invoice state is "Paid"
        self.assertEqual(self.invoice_ailos_1.payment_state, "paid")
        self.assertEqual(3.6, move.cnab_return_log_id.amount_total_tariff_charge)
        self.assertEqual(1000.0, move.cnab_return_log_id.amount_total_title)
        self.assertEqual(2, len(move.cnab_return_log_id.move_ids))
        expected_move_line_values_list = [
            [
                {
                    "account_name": "Account Receivable",
                    "debit": 0.0,
                    "credit": 300.0,
                },
                {
                    "account_name": "Banco AILOS",
                    "debit": 0.0,
                    "credit": 1.8,
                },
                {
                    "account_name": "Outras Despesas Financeiras - AVOID_TRAVIS_ERROR",
                    "debit": 1.8,
                    "credit": 0.0,
                },
                {
                    "account_name": "Banco AILOS",
                    "debit": 300.0,
                    "credit": 0.0,
                },
            ],
            [
                {
                    "account_name": "Account Receivable",
                    "debit": 0.0,
                    "credit": 700.0,
                },
                {
                    "account_name": "Banco AILOS",
                    "debit": 0.0,
                    "credit": 1.8,
                },
                {
                    "account_name": "Outras Despesas Financeiras - AVOID_TRAVIS_ERROR",
                    "debit": 1.8,
                    "credit": 0.0,
                },
                {
                    "account_name": "Banco AILOS",
                    "debit": 700.0,
                    "credit": 0.0,
                },
            ],
        ]
        moves = move.cnab_return_log_id.move_ids
        self._assert_move_entries(expected_move_line_values_list, moves)

    def test_banco_do_brasil_tarifa(self):
        mocked_response = [
            {
                "codigo_registro": "7",
                "codigo_ocorrencia": "02",
                "data_ocorrencia": "060224",
                "agencia_com_dv": "15298",
                "agencia_sem_dv": None,
                "cedente_com_dv": "0000060533",
                "convenio": None,
                "nosso_numero": "00000000000"
                + self.invoice_bancobrasil_1_own_numbers[1],
                "tipo_cobranca": None,
                "tipo_cobranca_anterior": None,
                "natureza_recebimento": None,
                "carteira_variacao": "019",
                "desconto": "0000000000000",
                "iof": "0000000000000",
                "carteira": "17",
                "comando": None,
                "data_liquidacao": None,
                "data_vencimento": "150224",
                "valor_titulo": "0000000040008",
                "banco_recebedor": "001",
                "agencia_recebedora_com_dv": "31747",
                "especie_documento": "01",
                "data_credito": "000000",
                "valor_tarifa": "0000234",
                "outras_despesas": None,
                "juros_desconto": None,
                "iof_desconto": None,
                "valor_abatimento": "0000000000000",
                "desconto_concedito": None,
                "valor_recebido": "0000000000000",
                "juros_mora": "0000000000000",
                "outros_recebimento": "0000000000000",
                "abatimento_nao_aproveitado": None,
                "valor_lancamento": None,
                "indicativo_lancamento": None,
                "indicador_valor": None,
                "valor_ajuste": None,
                "sequencial": "00002",
                "arquivo": None,
                "motivo_ocorrencia": [],
                "documento_numero": None,
            },
        ]
        self.journal = self.env.ref("l10n_br_account_payment_order.bb_journal")
        self.journal.floating_days = 2
        with mock.patch(
            _provider_class + "._get_brcobranca_retorno",
            return_value=mocked_response,
        ):
            file_name = get_resource_path(
                "l10n_br_account_payment_brcobranca",
                "tests",
                "data",
                "CNAB400BANCOBRASIL_tarifa.RET",
            )
            # Apesar de não haver ocorrências de liquidação,
            # Há ocorrências que geram cobrança de tarifas e
            # Lançamentos contábeis são criados
            # Nesse caso o retorno é um move (lançamento contabil)
            move = self._import_file(file_name)
        self.assertEqual(datetime.date(2024, 2, 8), move.date)
        self.assertEqual(2, move.journal_id.floating_days)
        self.assertEqual(2.34, move.cnab_return_log_id.amount_total_tariff_charge)
        self.assertEqual(400.08, move.cnab_return_log_id.amount_total_title)
        self.assertEqual(2, len(move.line_ids))
        self.assertEqual(
            "Banco BCO DO BRASIL S.A. - Conta 372", move.cnab_return_log_id.name
        )
        expected_move_line_values_list = [
            [
                {
                    "account_name": "Banco do Brasil",
                    "debit": 0.0,
                    "credit": 2.34,
                },
                {
                    "account_name": "Outras Despesas Financeiras - AVOID_TRAVIS_ERROR",
                    "debit": 2.34,
                    "credit": 0.0,
                },
            ]
        ]
        moves = move.cnab_return_log_id.move_ids
        self._assert_move_entries(expected_move_line_values_list, moves)

    def test_ailos_return_tarifa(self):
        mocked_response = [
            {
                "codigo_registro": "3",
                "codigo_ocorrencia": "23",
                "data_ocorrencia": "23112023",
                "agencia_com_dv": "001015",
                "agencia_sem_dv": None,
                "cedente_com_dv": "0000010713123",
                "convenio": None,
                "nosso_numero": "00000000000" + self.invoice_ailos_1_own_numbers[0],
                "tipo_cobranca": None,
                "tipo_cobranca_anterior": None,
                "natureza_recebimento": None,
                "carteira_variacao": None,
                "desconto": "0000000000000",
                "iof": None,
                "carteira": "1",
                "comando": None,
                "data_liquidacao": None,
                "data_vencimento": "07112023",
                "valor_titulo": "000000000152859",
                "banco_recebedor": "085",
                "agencia_recebedora_com_dv": "001015",
                "especie_documento": None,
                "data_credito": "06072021",
                "valor_tarifa": "00000000001700",
                "outras_despesas": "000000000000000",
                "juros_desconto": None,
                "iof_desconto": None,
                "valor_abatimento": "0000000000000",
                "desconto_concedito": None,
                "valor_recebido": "0000000000000",
                "juros_mora": "0000000000000",
                "outros_recebimento": None,
                "abatimento_nao_aproveitado": None,
                "valor_lancamento": None,
                "indicativo_lancamento": None,
                "indicador_valor": None,
                "valor_ajuste": None,
                "sequencial": "00023",
                "arquivo": None,
                "motivo_ocorrencia": [],
                "documento_numero": "03/01",
            },
        ]
        self.journal = self.env.ref("l10n_br_account_payment_order.ailos_journal")
        self.journal.floating_days = 2
        with mock.patch(
            _provider_class + "._get_brcobranca_retorno",
            return_value=mocked_response,
        ):
            file_name = get_resource_path(
                "l10n_br_account_payment_brcobranca",
                "tests",
                "data",
                "CNAB240AILOS_tarifa.RET",
            )

            # Apesar de não haver ocorrências de liquidação,
            # Há ocorrências que geram cobrança de tarifas e
            # Lançamentos contábeis são criados
            # Nesse caso o retorno é um move (lançamento contabil)
            move = self._import_file(file_name)
        self.assertEqual(datetime.date(2023, 11, 25), move.date)
        self.assertEqual(move._name, "account.move")
        self.assertEqual(
            "Banco COOP CENTRAL AILOS - Conta 373", move.cnab_return_log_id.name
        )
        self.assertEqual(17.0, move.cnab_return_log_id.amount_total_tariff_charge)
        self.assertEqual(1528.59, move.cnab_return_log_id.amount_total_title)
        self.assertEqual(2, len(move.line_ids))
        expected_move_line_values_list = [
            [
                {
                    "account_name": "Banco AILOS",
                    "debit": 0.0,
                    "credit": 17.0,
                },
                {
                    "account_name": "Outras Despesas Financeiras - AVOID_TRAVIS_ERROR",
                    "debit": 17.0,
                    "credit": 0.0,
                },
            ]
        ]
        moves = move.cnab_return_log_id.move_ids
        self._assert_move_entries(expected_move_line_values_list, moves)

    def test_ailos_return_tarifa_zero(self):
        mocked_response = [
            {
                "codigo_registro": "3",
                "codigo_ocorrencia": "23",
                "data_ocorrencia": "23112023",
                "agencia_com_dv": "001015",
                "agencia_sem_dv": None,
                "cedente_com_dv": "0000010713123",
                "convenio": None,
                "nosso_numero": "00000000000" + self.invoice_ailos_1_own_numbers[0],
                "tipo_cobranca": None,
                "tipo_cobranca_anterior": None,
                "natureza_recebimento": None,
                "carteira_variacao": None,
                "desconto": "0000000000000",
                "iof": None,
                "carteira": "1",
                "comando": None,
                "data_liquidacao": None,
                "data_vencimento": "07112023",
                "valor_titulo": "000000000152859",
                "banco_recebedor": "085",
                "agencia_recebedora_com_dv": "001015",
                "especie_documento": None,
                "data_credito": "06072021",
                "valor_tarifa": "00000000000000",
                "outras_despesas": "000000000000000",
                "juros_desconto": None,
                "iof_desconto": None,
                "valor_abatimento": "0000000000000",
                "desconto_concedito": None,
                "valor_recebido": "0000000000000",
                "juros_mora": "0000000000000",
                "outros_recebimento": None,
                "abatimento_nao_aproveitado": None,
                "valor_lancamento": None,
                "indicativo_lancamento": None,
                "indicador_valor": None,
                "valor_ajuste": None,
                "sequencial": "00023",
                "arquivo": None,
                "motivo_ocorrencia": [],
                "documento_numero": "03/01",
            },
        ]
        self.journal = self.env.ref("l10n_br_account_payment_order.ailos_journal")

        with mock.patch(
            _provider_class + "._get_brcobranca_retorno",
            return_value=mocked_response,
        ):
            file_name = get_resource_path(
                "l10n_br_account_payment_brcobranca",
                "tests",
                "data",
                "CNAB240AILOS_tarifa_zero.RET",
            )
            log = self._import_file(file_name)
        self.assertEqual(1528.59, log.amount_total_title)
        self.assertEqual("Banco COOP CENTRAL AILOS - Conta 373", log.name)
