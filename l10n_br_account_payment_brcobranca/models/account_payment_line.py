# Copyright 2020 Akretion
# @author Magno Costa <magno.costa@akretion.com.br>
# Copyright 2020 KMEE
# @author Luis Felipe Mileo <mileo@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import _, models
from odoo.exceptions import ValidationError

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

            # O Nº do Documento (posicoes 111 a 120) tem 10 caracteres e o
            # BRCobranca completa com zeros mas nao corta: um numero maior
            # desloca o resto da linha e o banco recusa o arquivo. O numero
            # segue o formato DOCUMENTO/PARCELA-TOTAL, entao sem o total de
            # parcelas ele cabe. O numero completo continua na identificacao
            # do titulo na empresa (posicoes 38 a 62, 25 caracteres).
            numero = str(linhas_pagamentos.get("numero") or "")
            if numero:
                result = numero
                numero_sem_zeros = numero.lstrip("0")
                numero_limpo = "".join(
                    char for char in numero_sem_zeros if char.isalnum()
                )
                if len(numero) > 25:
                    result = numero_sem_zeros
                    if len(numero_sem_zeros) > 25:
                        result = numero_limpo
                        if len(numero_limpo) > 25:
                            raise ValidationError(
                                _(
                                    "The lenght of the field 'documento' can't be more "
                                    "than 25 caracters:\n %(doc)s",
                                    doc=numero_limpo,
                                )
                            )

                linhas_pagamentos["documento"] = result

                # TODO: É melhor "cortar" o número silenciosamente
                #  ou mostrar o erro?
                # linhas_pagamentos["numero"] = numero[-10:]
                if len(result) > 10:
                    result = numero_sem_zeros
                    if len(numero_sem_zeros) > 10:
                        result = numero_limpo
                        if len(numero_limpo) > 10:
                            raise ValidationError(
                                _(
                                    "The lenght of the field 'numero' can't be more "
                                    "than 10 caracters:\n %(num)s",
                                    num=numero_limpo,
                                )
                            )
                linhas_pagamentos["numero"] = result

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

    @staticmethod
    def _get_sicredi_nosso_numero(agencia, posto, beneficiario, ano, byte_idt, seq):
        """Build the Sicredi CNAB 240 "Nosso Número" (AA/BXXXXX-D).

        Manual Sicredi CNAB 240, items 4.4 and 4.5: the check digit is
        módulo 11 over agência (4) + posto (2) + beneficiário (5) + ano (2)
        + byte de geração (1) + sequencial (5). The "/" and "-" are only
        presentation characters and are not sent in the CNAB.
        """
        sequencial = "".join(ch for ch in str(seq) if ch.isdigit()).zfill(5)[-5:]
        base_dv = (
            agencia + str(posto).zfill(2) + beneficiario + ano + byte_idt + sequencial
        )
        dv = modulo11(base_dv, 9, 0)
        return ano + byte_idt + sequencial + str(dv)

    def _prepare_bank_line_sicredi(self, cnab_config, linhas_pagamentos):
        # Manual Sicredi CNAB 240 - itens 4.4 e 4.5.
        # A data de referência deve ser a da fatura, não a atual, para evitar
        # divergência de ano na virada do ano (Manual Sicredi item 4.4: o ano
        # "pode ser diferente do ano corrente").
        bank_account_id = self.order_id.journal_id.bank_account_id
        ano = self.move_line_id.move_id.invoice_date.strftime("%y")
        linhas_pagamentos["nosso_numero"] = self._get_sicredi_nosso_numero(
            bank_account_id.bra_number,
            cnab_config.boleto_post,
            cnab_config.cnab_company_bank_code,
            ano,
            str(cnab_config.boleto_byte_idt),
            self.own_number,
        )

        # Manual Sicredi CNAB 240 - item 8.5 (Segmento Q).
        # As posições 114-128 são CNAB (Sem preenchimento), mas o BRCobranca
        # escreve o bairro do pagador nesse campo seguindo o layout FEBRABAN.
        # Para o Sicredi o bairro deve ser enviado em branco.
        linhas_pagamentos["bairro_sacado"] = ""

        # Multa - Manual Sicredi CNAB 240, item 14.3R: "No Sicredi a multa
        # só pode ser informada em valor percentual" (código "2"). Nunca
        # preencher como "0" (isento), o Segmento R exige o código da multa.
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
            # Manual Sicredi CNAB 240 itens 30.3P, 08.3R e 11.3R:
            # 0 = Sem desconto, 1 = Valor fixo até a data informada,
            # 2 = Percentual até a data informada, 3 = Valor por antecipação
            # (dias corridos), 7 = Cancelamento de desconto. Para o código 0
            # o valor e a data do desconto devem ser zerados.

            # Apesar das Documentações dos Bancos dizerem que estão seguindo
            # um "Padrão" na realidade:
            # Banco     | Cod Banco | Possíveis Códigos de Desconto |
            #           |           | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 |
            # ----------|-----------|---|---|---|---|---|---|---|---|
            # Ailos     |    085    | X | X |   |   |   |   |   |   |
            # Bradesco  |    237    |   | X | X | X | X | X | X | X |
            # CEF       |    104    | X | X | X |   |   |   |   |   |
            # Santander |    033    | X | X | X | X |   |   |   |   |
            # Sicred    |    748    | X | X | X | X |   |   |   | X |
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
                    # Código "0" = Sem desconto (Manual Sicredi CNAB 240
                    # item 30.3P): valor e data do desconto são zerados.
                    discount_code = "0"

            if discount_code:
                linhas_pagamentos["cod_desconto"] = discount_code

        return linhas_pagamentos
