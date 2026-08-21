# Copyright 2020 Akretion
# @author Magno Costa <magno.costa@akretion.com.br>
# Copyright 2020 KMEE
# @author Luis Felipe Mileo <mileo@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from datetime import date

from erpbrasil.base import misc

from odoo import models

from ..constants.br_cobranca import modulo11

_logger = logging.getLogger(__name__)


class AccountPaymentLine(models.Model):
    _inherit = "account.payment.line"

    def _prepare_bank_line_unicred(self, cnab_config, linhas_pagamentos):
        # Preenchendo valores que se forem vazios geram erro
        linhas_pagamentos["codigo_protesto"] = (
            cnab_config.boleto_protest_code_id.code or "3"
        )
        linhas_pagamentos["dias_protesto"] = cnab_config.boleto_days_protest or "0"

        # Isento de Multa caso não exista percentual
        linhas_pagamentos["codigo_multa"] = "3"

        # Isento de Mora
        linhas_pagamentos["tipo_mora"] = "5"

        # Tamanho do campo não pode se maior do que 10
        doc_number = str(self.document_number)
        if len(doc_number) > 10:
            start_point = len(self.document_number) - 10
            doc_number = doc_number[start_point : len(self.document_number)]

        linhas_pagamentos["numero"] = doc_number

    def _prepare_cod_primeira_instrucao_protest(self, cnab_config, linhas_pagamentos):
        if self.instruction_move_code_id.code == cnab_config.sending_code_id.code:
            linhas_pagamentos["cod_primeira_instrucao"] = (
                cnab_config.boleto_protest_code_id.code or "00"
            )

    def _prepare_bank_line_itau(self, cnab_config, linhas_pagamentos):
        if cnab_config.payment_method_code == "400":
            self._prepare_cod_primeira_instrucao_protest(cnab_config, linhas_pagamentos)

    def _prepare_bank_line_banco_brasil(self, cnab_config, linhas_pagamentos):
        self._prepare_cod_primeira_instrucao_protest(cnab_config, linhas_pagamentos)

    def _prepare_bank_line_santander(self, cnab_config, linhas_pagamentos):
        if cnab_config.payment_method_id.code == "400":
            nosso_numero = linhas_pagamentos["nosso_numero"]
            # O campo deve ter tamanho 7 caso a Sequencia não esteja configurada
            # corretamente é tratado aqui, talvez deva ser feito na validação
            if len(nosso_numero) > 7:
                start_point = len(nosso_numero) - 7
                nosso_numero = nosso_numero[start_point : len(nosso_numero)]

            dv = modulo11(nosso_numero, 9, 0)
            linhas_pagamentos["nosso_numero"] = str(nosso_numero) + str(dv)
        elif cnab_config.payment_method_id.code == "240":
            linhas_pagamentos[
                "codigo_baixa"
            ] = cnab_config.write_off_devolution_code_id.code
            linhas_pagamentos["dias_baixa"] = str(
                cnab_config.write_off_devolution_number_of_days
            )
            # Os dados de multa e desconto também são obrigatórios no segmento R
            linhas_pagamentos["codigo_multa"] = (
                cnab_config.boleto_fee_code_id.code or "0"
            )
            linhas_pagamentos["percentual_multa"] = cnab_config.boleto_fee_perc or 0.0
            if self.discount_value:
                linhas_pagamentos["data_desconto"] = self.date.strftime("%Y/%m/%d")
                linhas_pagamentos["valor_desconto"] = self.discount_value

    def _prepare_bank_line_sicredi(self, cnab_config, linhas_pagamentos):
        # Manual Sicredi CNAB 240 - itens 4.4 e 4.5.
        # Nosso Número no formato AA/BXXXXX-D, onde:
        # AA = Ano, B = Byte de geração, XXXXX = Sequencial e D = DV.
        # O DV (módulo 11) é calculado sobre a base agência + posto + beneficiário
        # + ano + byte + sequencial (5 dígitos, com zeros à esquerda).
        bank_account_id = self.order_id.journal_id.bank_account_id
        # XXXXX = Número livre de 00000 a 99999, portanto o sequencial deve
        # ter exatamente 5 dígitos (zeros à esquerda).
        sequencial = "".join(
            ch for ch in str(self.own_number) if ch.isdigit()
        ).zfill(5)[-5:]
        ano = str(date.today().year)[2:]
        byte_idt = str(cnab_config.boleto_byte_idt)
        agencia = bank_account_id.bra_number
        posto = str(cnab_config.boleto_post).zfill(2)
        beneficiario = misc.punctuation_rm(bank_account_id.acc_number).zfill(5)

        base_dv = agencia + posto + beneficiario + ano + byte_idt + sequencial
        dv = modulo11(base_dv, 9, 0)
        linhas_pagamentos["nosso_numero"] = (
            ano + byte_idt + sequencial + str(dv)
        )

        # Manual Sicredi CNAB 240 - item 8.5 (Segmento Q).
        # As posições 114-128 são CNAB (Sem preenchimento), mas o BRCobranca
        # escreve o bairro do pagador nesse campo seguindo o layout FEBRABAN.
        # Para o Sicredi o bairro deve ser enviado em branco.
        linhas_pagamentos["bairro_sacado"] = ""

        # Multa - obrigatório no Segmento R do Sicredi:
        # 1 = valor fixo | 2 = percentual, nunca deve ser preenchido como 0.
        if cnab_config.boleto_fee_code_id:
            linhas_pagamentos["codigo_multa"] = cnab_config.boleto_fee_code_id.code
        elif cnab_config.boleto_fee_perc:
            linhas_pagamentos["codigo_multa"] = "2"
        if cnab_config.boleto_fee_perc:
            linhas_pagamentos["percentual_multa"] = cnab_config.boleto_fee_perc

    def prepare_bank_payment_line(self, bank_name_brcobranca):
        cnab_config = self.order_id.payment_mode_id.cnab_config_id
        linhas_pagamentos = self._prepare_boleto_line_vals()

        # Casos onde o Banco além dos principais campos possui campos
        # específicos, dos casos por enquanto mapeados, se estiver vendo
        # um caso que está faltando por favor considere fazer um
        # PR para ajudar
        if hasattr(self, f"_prepare_bank_line_{bank_name_brcobranca.name}"):
            bank_method = getattr(
                self, f"_prepare_bank_line_{bank_name_brcobranca.name}"
            )
            bank_method(cnab_config, linhas_pagamentos)

        # Cada Banco pode possuir seus Codigos de Instrução
        if self.instruction_move_code_id.code == cnab_config.sending_code_id.code:
            if cnab_config.boleto_fee_code_id:
                linhas_pagamentos["codigo_multa"] = cnab_config.boleto_fee_code_id.code
                if cnab_config.boleto_fee_perc:
                    linhas_pagamentos["percentual_multa"] = cnab_config.boleto_fee_perc

            # Juros Mora
            # Casos Isento podem não ter boleto_interest_perc
            if cnab_config.boleto_interest_code_id:
                linhas_pagamentos[
                    "tipo_mora"
                ] = cnab_config.boleto_interest_code_id.code
            if cnab_config.boleto_interest_perc:
                # Padrão 'Valor por Dia', porque os casos Itau, Santander e Nordeste
                # 400 pelas Documentações não tem um 'Código Mora' mas pelo código
                # do BRCobranca parece que usam esse caso.
                valor_mora = self.company_currency_id.round(
                    self.amount_currency
                    * ((cnab_config.boleto_interest_perc / 100) / 30),
                )
                if cnab_config.boleto_interest_code_id:
                    if cnab_config.boleto_interest_code_id.code == "2":
                        valor_mora = cnab_config.boleto_interest_perc

                linhas_pagamentos["valor_mora"] = valor_mora

            if self.discount_value:
                linhas_pagamentos["data_desconto"] = self.date.strftime("%Y/%m/%d")
                linhas_pagamentos["valor_desconto"] = self.discount_value

            # Protesto
            if cnab_config.boleto_protest_code_id:
                linhas_pagamentos[
                    "codigo_protesto"
                ] = cnab_config.boleto_protest_code_id.code
                if cnab_config.boleto_days_protest:
                    linhas_pagamentos["dias_protesto"] = cnab_config.boleto_days_protest

            # Desconto
            # Código adotado pela FEBRABAN para identificação do desconto.
            # Domínio: 0 = Isento | 1 = Valor Fixo

            # Apesar das Documentações dos Bancos dizerem que estão seguindo
            # um "Padrão" na realidade:
            # Banco     | Cod Banco | Possíveis Códigos de Desconto |
            #           |           | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 |
            # ----------|-----------|---|---|---|---|---|---|---|---|
            # Ailos     |    085    | X | X |   |   |   |   |   |   |
            # Bradesco  |    237    |   | X | X | X | X | X | X | X |
            # CEF       |    104    | X | X | X |   |   |   |   |   |
            # Santander |    033    | X | X | X | X |   |   |   |   |
            # Sicred    |    748    |   | X | X | X |   |   |   | X |
            # Unicred   |    136    | X | X |   |   |   |   |   |   |

            discount_code = False
            if self.discount_value:
                # Apenas para inicialmente evitar erro no caso do CNAB Config
                # não está com valor no 'Codigo de Desconto'.
                # TODO: Considerar remover e deixar apenas o 'Código de Desconto'
                #  e dependendo retornar um Warning sobre a falta da informação.
                discount_code = "1"

                if cnab_config.boleto_discount_code_id:
                    discount_code = cnab_config.boleto_discount_code_id.code
            else:
                if cnab_config.bank_code_bc in ("085", "104", "033", "136", "748") or (
                    cnab_config.bank_code_bc == "001"
                    and cnab_config.payment_method_id.code == "240"
                ):
                    # Casos mapeados que enviam Zero para quando não tem valor
                    discount_code = "0"

            if discount_code:
                linhas_pagamentos["cod_desconto"] = discount_code

        return linhas_pagamentos
