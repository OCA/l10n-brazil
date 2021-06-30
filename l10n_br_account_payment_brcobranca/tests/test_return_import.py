# Copyright 2021 Akretion - Raphaël Valyi <raphael.valyi@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)
# Copyright (C) 2021-Today - Akretion (<http://www.akretion.com>).
# @author Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
import os
from unittest import mock

from odoo import tools
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
        tools.convert_file(
            cls.cr,
            "account",
            get_resource_path("account", "test", "account_minimal_test.xml"),
            {},
            "init",
            False,
            "test",
        )
        cls.account_move_obj = cls.env["account.move"]
        cls.account_move_line_obj = cls.env["account.move.line"]
        cls.cnab_log_obj = cls.env["l10n_br_cnab.return.log"]
        cls.account_id = cls.env.ref("account.a_recv")
        cls.bank_account = cls.env.ref("account.bnk")
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

        cls.journal = cls.env.ref("l10n_br_account_payment_order.unicred_journal")

        # I validate invoice by creating on
        cls.invoice_unicred_1.action_invoice_open()
        cls.invoice_unicred_2.action_invoice_open()

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

        payment_order = cls.env["account.payment.order"].search(
            [("payment_mode_id", "=", cls.invoice_unicred_1.payment_mode_id.id)]
        )

        # Open payment order
        payment_order.draft2open()

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
                    payment_order.open2generated()
        else:
            payment_order.open2generated()

        # Confirm Upload
        payment_order.generated2uploaded()

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

    def test_valor_menor_1(self):

        mocked_response = [
            {
                "codigo_registro": "1",
                "codigo_ocorrencia": "02",
                "data_ocorrencia": None,
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
                "data_ocorrencia": None,
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
                "data_ocorrencia": None,
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
            # Se não for um codigo cnab de liquidação retorna apenas o LOG criado.
            log = self._import_file(file_name)

        self.assertEqual("Banco UNICRED - Conta 371", log.name)

    def test_valor_menor_2(self):

        mocked_response = [
            {
                "codigo_registro": "1",
                "codigo_ocorrencia": "06",
                "data_ocorrencia": None,
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
                "data_ocorrencia": None,
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
                "data_ocorrencia": None,
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
            # Se for um codigo cnab de liquidação retorna as account.move criadas.
            moves = self._import_file(file_name)

        self.assertEqual("Retorno CNAB - Banco UNICRED - Conta 371", moves.name)
        # I check that the invoice state is "Paid"
        self.assertEqual(self.invoice_unicred_1.state, "paid")

    def test_valor_maior_3(self):

        mocked_response = [
            {
                "codigo_registro": "1",
                "codigo_ocorrencia": "02",
                "data_ocorrencia": None,
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
                "data_ocorrencia": None,
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
                "data_ocorrencia": None,
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
            # Se não for um codigo cnab de liquidação retorna apenas o LOG criado.
            log = self._import_file(file_name)

        self.assertEqual("Banco UNICRED - Conta 371", log.name)

    def test_valor_maior_4(self):

        mocked_response = [
            {
                "codigo_registro": "1",
                "codigo_ocorrencia": "06",
                "data_ocorrencia": None,
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
                "data_ocorrencia": None,
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
                "data_ocorrencia": None,
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
            # Se for um codigo cnab de liquidação retorna as account.move criadas
            moves = self._import_file(file_name)

        self.assertEqual("Retorno CNAB - Banco UNICRED - Conta 371", moves.name)
        # I check that the invoice state is "Paid"
        self.assertEqual(self.invoice_unicred_2.state, "paid")
