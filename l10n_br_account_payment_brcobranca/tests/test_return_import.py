# Copyright (C) 2021-Today - Akretion (<http://www.akretion.com>).
# @author Raphaël Valyi <raphael.valyi@akretion.com.br>
# @author Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import tagged

from odoo.addons.l10n_br_account_payment_brcobranca.tests.common import (
    TestBrAccountPaymentOderCommon,
)


@tagged("post_install", "-at_install")
class TestReturnImport(TestBrAccountPaymentOderCommon):
    def _check_updated_own_numbers(self, invoice):
        # Para evitar erros nos testes de variação da Sequencia do
        # Nosso Numero/own_number quando se roda mais de uma vez
        result = []
        for line in invoice.financial_move_line_ids:
            # Arquivo de retorno vem
            # UNICRED = NOSSO NUMERO + Digito Verificador
            # AILOS = NOSSO NUMERO
            own_number = line.own_number
            if line.journal_payment_mode_id.bank_id.code_bc != "085":
                own_number += "0"

            result.append(own_number)

        return result

    def _get_mocked_response_unicred_valor_menor(self, invoice_unicred_cnab_400):
        # Para evitar erros nos testes de variação da Sequencia do
        # Nosso Numero/own_number quando se roda mais de uma vez ou
        # devido a diferença entre os comandos feitos pelo Travis
        updated_own_numbers = self._check_updated_own_numbers(invoice_unicred_cnab_400)
        test_run_more_than_one_time = True
        if updated_own_numbers[0] == "00000000010":
            test_run_more_than_one_time = False

        mocked_response = []
        mocked_response.append(
            [
                {
                    "codigo_registro": "1",
                    "codigo_ocorrencia": "02",
                    "data_ocorrencia": None,
                    "agencia_com_dv": None,
                    "agencia_sem_dv": "1234",
                    "cedente_com_dv": "000003719",
                    "convenio": None,
                    # "nosso_numero": "00000000000000010",
                    "nosso_numero": updated_own_numbers[0],
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
                    "nosso_numero": updated_own_numbers[1],
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
        )

        # Importando o segundo arquivo que gera o Pagamento
        mocked_response.append(
            [
                {
                    "codigo_registro": "1",
                    "codigo_ocorrencia": "06",
                    "data_ocorrencia": None,
                    "agencia_com_dv": None,
                    "agencia_sem_dv": "1234",
                    "cedente_com_dv": "000003719",
                    "convenio": None,
                    # "nosso_numero": "00000000000000090",
                    "nosso_numero": updated_own_numbers[0],
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
                    "nosso_numero": updated_own_numbers[1],
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
        )

        return mocked_response, test_run_more_than_one_time

    def _get_mocked_response_unicred_valor_maior(self, invoice_unicred_cnab_400):
        updated_own_numbers = self._check_updated_own_numbers(invoice_unicred_cnab_400)
        test_run_more_than_one_time = True
        if updated_own_numbers[0] == "00000000030":
            test_run_more_than_one_time = False

        mocked_response = []
        mocked_response.append(
            [
                {
                    "codigo_registro": "1",
                    "codigo_ocorrencia": "02",
                    "data_ocorrencia": None,
                    "agencia_com_dv": None,
                    "agencia_sem_dv": "1234",
                    "cedente_com_dv": "000003719",
                    "convenio": None,
                    # "nosso_numero": "00000000000000030",
                    "nosso_numero": updated_own_numbers[0],
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
                    "nosso_numero": updated_own_numbers[1],
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
        )

        # Importação do Arquivo que Gera Pagamento
        mocked_response.append(
            [
                {
                    "codigo_registro": "1",
                    "codigo_ocorrencia": "06",
                    "data_ocorrencia": None,
                    "agencia_com_dv": None,
                    "agencia_sem_dv": "1234",
                    "cedente_com_dv": "000003719",
                    "convenio": None,
                    # "nosso_numero": "00000000000000110",
                    "nosso_numero": updated_own_numbers[0],
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
                    "nosso_numero": updated_own_numbers[1],
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
        )

        return mocked_response, test_run_more_than_one_time

    def _get_mocked_response_ailos(self, invoice_ailos_cnab_240):
        updated_own_numbers = self._check_updated_own_numbers(invoice_ailos_cnab_240)
        test_run_more_than_one_time = True
        if updated_own_numbers[0] == "000000001":
            test_run_more_than_one_time = False

        mocked_response = [
            {
                "codigo_registro": "03",
                "codigo_ocorrencia": "06",
                "data_ocorrencia": None,
                "agencia_com_dv": None,
                "agencia_sem_dv": "1234",
                "cedente_com_dv": "000003719",
                "convenio": None,
                "nosso_numero": updated_own_numbers[0],
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
                "data_ocorrencia": None,
                "agencia_com_dv": None,
                "agencia_sem_dv": "1234",
                "cedente_com_dv": "000003719",
                "convenio": None,
                "nosso_numero": updated_own_numbers[1],
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

        return mocked_response, test_run_more_than_one_time

    def test_1_unicred_cnab400_valor_menor(self):
        """
        Test UNICRED CNAB 400 'Boleto, Arquivo de Remessa' and import two 'Arquivo
        de Retorno' the first to Confirm the CNAB Instruction, only generate a LOG,
        and the second for generate the Payment when the received Value are less
        than Debit in Odoo.
        """

        invoice_unicred_cnab_400 = self.env.ref(
            "l10n_br_account_payment_order.demo_invoice_payment_order_unicred_cnab400"
        )
        self._run_boleto_remessa(
            invoice_unicred_cnab_400,
            "boleto_teste_unicred400.pdf",
            "teste_remessa-unicred_400-1.REM",
        )

        (
            mocked_response,
            test_run_more_than_one_time,
        ) = self._get_mocked_response_unicred_valor_menor(invoice_unicred_cnab_400)

        log = self._run_import_return_file(
            "CNAB400UNICRED_valor_menor_1.RET",
            self.env.ref("l10n_br_account_payment_order.unicred_journal"),
            test_run_more_than_one_time,
            mocked_response[0],
        )
        self.assertEqual("Banco UNICRED - Conta 371", log.name)

        # Importando o segundo arquivo que gera o Pagamento
        moves = self._run_import_return_file(
            "CNAB400UNICRED_valor_menor_2.RET",
            self.env.ref("l10n_br_account_payment_order.unicred_journal"),
            test_run_more_than_one_time,
            mocked_response[1],
        )
        self.assertEqual("Retorno CNAB - Banco UNICRED - Conta 371", moves.ref)
        # I check that the invoice state is "Paid"
        self.assertEqual(invoice_unicred_cnab_400.payment_state, "paid")

    def test_2_unicred_cnab400_valor_maior(self):
        """
        Test UNICRED CNAB 400 'Boleto, Arquivo de Remessa' and import two 'Arquivo
        de Retorno' the first to Confirm the CNAB Instruction, only generate a LOG,
        and the second for generate the Payment when the received Value are greater
        than Debit in Odoo.
        """

        invoice_unicred_cnab_400 = self.env.ref(
            "l10n_br_account_payment_brcobranca."
            "demo_invoice_brcobranca_unicred_cnab400"
        )
        self._run_boleto_remessa(
            invoice_unicred_cnab_400,
            "boleto_teste_unicred400.pdf",
            "teste_remessa-unicred_400-1.REM",
        )

        (
            mocked_response,
            test_run_more_than_one_time,
        ) = self._get_mocked_response_unicred_valor_maior(invoice_unicred_cnab_400)

        log = self._run_import_return_file(
            "CNAB400UNICRED_valor_maior_3.RET",
            self.env.ref("l10n_br_account_payment_order.unicred_journal"),
            test_run_more_than_one_time,
            mocked_response[0],
        )
        self.assertEqual("Banco UNICRED - Conta 371", log.name)

        # Importação do Arquivo que Gera Pagamento
        moves = self._run_import_return_file(
            "CNAB400UNICRED_valor_maior_4.RET",
            self.env.ref("l10n_br_account_payment_order.unicred_journal"),
            test_run_more_than_one_time,
            mocked_response[1],
        )
        self.assertEqual("Retorno CNAB - Banco UNICRED - Conta 371", moves.ref)
        # I check that the invoice state is "Paid"
        self.assertEqual(invoice_unicred_cnab_400.payment_state, "paid")

    def test_3_ailos_cnab_240(self):
        """
        Test AILOS CNAB 240 'Boleto, Arquivo de Remessa' and import one
        'Arquivo de Retorno' for generate the Payment.
        """

        invoice_ailos_cnab_240 = self.env.ref(
            "l10n_br_account_payment_order.demo_invoice_payment_order_ailos_cnab240"
        )
        self._run_boleto_remessa(
            invoice_ailos_cnab_240,
            "boleto_teste_ailos_cnab240.pdf",
            "teste_remessa_ailos240.REM",
        )

        mocked_response, test_run_more_than_one_time = self._get_mocked_response_ailos(
            invoice_ailos_cnab_240
        )

        moves = self._run_import_return_file(
            "CNAB240AILOS.RET",
            self.env.ref("l10n_br_account_payment_order.ailos_journal"),
            test_run_more_than_one_time,
            mocked_response,
        )
        self.assertEqual(
            "Retorno CNAB - Banco COOP CENTRAL AILOS - Conta 373", moves.ref
        )
        # I check that the invoice state is "Paid"
        self.assertEqual(invoice_ailos_cnab_240.payment_state, "paid")

    def test_4_simulate_mocked_response(self):
        """
        Simulate Mocked Response, just to keep the Code Coverage.
        """

        # Caso que tem uma Resposta Mocked
        invoice_unicred_cnab_400 = self.env.ref(
            "l10n_br_account_payment_order.demo_invoice_payment_order_unicred_cnab400"
        )
        self._run_boleto_remessa(
            invoice_unicred_cnab_400,
            "boleto_teste_unicred400.pdf",
            "teste_remessa-unicred_400-1.REM",
        )

        (
            mocked_response,
            test_run_more_than_one_time,
        ) = self._get_mocked_response_unicred_valor_menor(invoice_unicred_cnab_400)

        self._run_import_return_file(
            "CNAB400UNICRED_valor_menor_1.RET",
            self.env.ref("l10n_br_account_payment_order.unicred_journal"),
            test_run_more_than_one_time,
            mocked_response[0],
        )

    def test_5_nordeste_cnab_400(self):
        """
        Test import Nordeste Bank CNAB 400, the case has different 'Return Code'
        for refused 'Instruction Code'.
        """

        invoice_nordeste_cnab_400 = self.env.ref(
            "l10n_br_account_payment_order."
            "demo_invoice_payment_order_nordeste_cnab400"
        )
        self._run_boleto_remessa(
            invoice_nordeste_cnab_400,
            "boleto_teste_nordeste400.pdf",
            "teste_remessa_nordeste400.REM",
        )
        updated_own_numbers = self._check_updated_own_numbers(invoice_nordeste_cnab_400)
        test_run_more_than_one_time = True
        if updated_own_numbers[0] == "00000010":
            test_run_more_than_one_time = False

        log = self._run_import_return_file(
            "CNAB400NORDESTE.RET",
            self.env.ref("l10n_br_account_payment_order.nordeste_journal"),
            test_run_more_than_one_time,
        )
        for line in log.event_ids:
            self.assertEqual("51-Entrada Rejeitada.", line.occurrences)
            self.assertEqual("not_accepted", line.move_line_id.cnab_state)

    def test_6_simulate_without_mocked_response(self):
        """
        Simulate without Mocked Response, just to keep the Code Coverage.
        """
        # Caso Sem uma Resposta Mocked
        invoice_nordeste_cnab_400 = self.env.ref(
            "l10n_br_account_payment_order."
            "demo_invoice_payment_order_nordeste_cnab400"
        )
        self._run_boleto_remessa(
            invoice_nordeste_cnab_400,
            "boleto_teste_nordeste400.pdf",
            "teste_remessa_nordeste400.REM",
        )
        test_run_more_than_one_time = True
        self._run_import_return_file(
            "CNAB400NORDESTE.RET",
            self.env.ref("l10n_br_account_payment_order.nordeste_journal"),
            test_run_more_than_one_time,
        )
