# Copyright 2020 Akretion
# @author Magno Costa <magno.costa@akretion.com.br>
# Copyright 2020 KMEE
# @author Luis Felipe Mileo <mileo@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import models

_logger = logging.getLogger(__name__)


class AccountPaymentLine(models.Model):
    _inherit = "account.payment.line"

    def _prepare_bank_line_ailos(self, payment_mode_id, linhas_pagamentos):
        if self.discount_value:
            # Código adotado pela FEBRABAN para identificação do desconto.
            # Domínio:
            # 0 = Isento
            # 1 = Valor Fixo
            linhas_pagamentos["cod_desconto"] = "1"

    def _prepare_bank_line_unicred(self, payment_mode_id, linhas_pagamentos):
        # TODO - Valores padrões ?
        #  Estou preenchendo valores que se forem vazios geram erro
        #  os campos parecem estar usando uma Seleção que é definida
        #  na Febraban, isso acontece em todos os casos( CNAB 240/400 ) ?
        #  Isso deveria ser feito para o CNAB de outros Bancos ?
        #  Na criação dos campos houve a opção de deixa-los com o tipo
        #  CHAR ao invês de Selection por essa falta de padrão.
        linhas_pagamentos["codigo_protesto"] = (
            payment_mode_id.boleto_protest_code or "3"
        )
        linhas_pagamentos["dias_protesto"] = payment_mode_id.boleto_days_protest or "0"

        # Código adotado pela FEBRABAN para identificação
        # do tipo de pagamento de multa.
        # Domínio:
        # ‘1’ = Valor Fixo (R$)
        # ‘2’ = Taxa (%)
        # ‘3’ = Isento
        # Isento de Multa caso não exista percentual
        linhas_pagamentos["codigo_multa"] = "3"

        # Isento de Mora
        linhas_pagamentos["tipo_mora"] = "5"

        # TODO
        # Código adotado pela FEBRABAN para identificação do desconto.
        # Domínio:
        # 0 = Isento
        # 1 = Valor Fixo
        linhas_pagamentos["cod_desconto"] = "0"

        # Tamanho do campo não pode se maior do que 10
        doc_number = str(self.document_number)
        if len(doc_number) > 10:
            start_point = len(self.document_number) - 10
            doc_number = doc_number[start_point : len(self.document_number)]

        linhas_pagamentos["numero"] = doc_number

        if self.discount_value:
            linhas_pagamentos["cod_desconto"] = "1"

    def _prepare_bank_line_banco_brasil(self, payment_mode_id, linhas_pagamentos):
        if (
            self.mov_instruction_code_id.code
            == payment_mode_id.cnab_sending_code_id.code
        ):
            linhas_pagamentos["cod_primeira_instrucao"] = (
                payment_mode_id.boleto_protest_code or "00"
            )

    # Caso Santander 400 precisa enviar o Nosso Numero com DV isso não acontece no
    # 240, por enquanto é o único caso mapeado.
    # Houve um PR https://github.com/kivanio/brcobranca/pull/236 na lib buscando
    # resolver isso e foi apontando a contradição em ter para esse mesmo banco no
    # caso do 400 a necessidade de informar o DV mas não precisar no 240,
    # mas o mantedor da biblioteca não aceito a alteração.
    # A melhor solução talvez seja ver a possibilidade de incluir ou fazer algo
    # semelhante ao git-aggregator https://github.com/acsone/git-aggregator
    # na API e com isso incluir um commit de outro repositorio que faça essa
    # simples alteração porém mantendo a API ligada diretamente ao repo pricipal
    # do BRcobranca, já que não existe o interesse em manter um Fork e um simples
    # commit resolve o problema, por enquanto o calculo esta sendo feito aqui, se
    # necessário ou isso for útil para outros casos pode ser visto de migrar esse
    # calculo do modulo11 para um lugar genereico e facilitar seu uso exemplo
    # l10n_br_account_payment_order/tools.py
    def modulo11(self, num, base=9, r=0):
        soma = 0
        fator = 2
        for c in reversed(num):
            soma += int(c) * fator
            if fator == base:
                fator = 1
            fator += 1
        if r == 0:
            soma = soma * 10
            digito = soma % 11
            if digito == 10:
                digito = 0
            return digito
        if r == 1:
            resto = soma % 11
            return resto

    def _prepare_bank_line_santander(self, payment_mode_id, linhas_pagamentos):
        if payment_mode_id.payment_method_code == "400":
            nosso_numero = linhas_pagamentos["nosso_numero"]
            # O campo deve ter tamanho 7 caso a Sequencia não esteja configurada
            # corretamente é tratado aqui, talvez deva ser feito na validação
            if len(nosso_numero) > 7:
                start_point = len(nosso_numero) - 7
                nosso_numero = nosso_numero[start_point : len(nosso_numero)]

            dv = self.modulo11(nosso_numero, 9, 0)
            linhas_pagamentos["nosso_numero"] = str(nosso_numero) + str(dv)

    def prepare_bank_payment_line(self, bank_name_brcobranca):
        payment_mode_id = self.order_id.payment_mode_id
        linhas_pagamentos = self._prepare_boleto_line_vals()

        # Casos onde o Banco além dos principais campos possui campos
        # específicos, dos casos por enquanto mapeados, se estiver vendo
        # um caso que está faltando por favor considere fazer um
        # PR para ajudar
        if hasattr(self, f"_prepare_bank_line_{bank_name_brcobranca.name}"):
            bank_method = getattr(
                self, f"_prepare_bank_line_{bank_name_brcobranca.name}"
            )
            bank_method(payment_mode_id, linhas_pagamentos)

        # Cada Banco pode possuir seus Codigos de Instrução
        if (
            self.mov_instruction_code_id.code
            == payment_mode_id.cnab_sending_code_id.code
        ):
            if payment_mode_id.boleto_fee_perc:
                linhas_pagamentos["codigo_multa"] = payment_mode_id.boleto_fee_code
                linhas_pagamentos["percentual_multa"] = payment_mode_id.boleto_fee_perc

            if payment_mode_id.boleto_interest_perc:
                linhas_pagamentos["tipo_mora"] = payment_mode_id.boleto_interest_code
                # TODO - É padrão em todos os bancos ?
                # Código adotado pela FEBRABAN para identificação do tipo de
                # pagamento de mora de juros.
                # Domínio:
                # ‘1’ = Valor Diário (R$)
                # ‘2’ = Taxa Mensal (%)
                # ‘3’= Valor Mensal (R$) *
                # ‘4’ = Taxa diária (%)
                # ‘5’ = Isento
                # *OBSERVAÇÃO:
                # ‘3’ - Valor Mensal (R$): a CIP não acata valor mensal,
                # segundo manual. Cógido mantido
                # para Correspondentes que ainda utilizam.
                # Isento de Mora caso não exista percentual
                if payment_mode_id.boleto_interest_code == "1":
                    linhas_pagamentos["valor_mora"] = self.company_currency_id.round(
                        self.amount_currency
                        * ((payment_mode_id.boleto_interest_perc / 100) / 30),
                    )
                if payment_mode_id.boleto_interest_code == "2":
                    linhas_pagamentos[
                        "valor_mora"
                    ] = payment_mode_id.boleto_interest_perc

            if self.discount_value:
                linhas_pagamentos["data_desconto"] = self.date.strftime("%Y/%m/%d")
                linhas_pagamentos["valor_desconto"] = self.discount_value

            # Protesto
            if payment_mode_id.boleto_protest_code:
                linhas_pagamentos[
                    "codigo_protesto"
                ] = payment_mode_id.boleto_protest_code
                if payment_mode_id.boleto_days_protest:
                    linhas_pagamentos[
                        "dias_protesto"
                    ] = payment_mode_id.boleto_days_protest

        return linhas_pagamentos
