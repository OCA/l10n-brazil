# Copyright 2020 Akretion
# @author Magno Costa <magno.costa@akretion.com.br>
# Copyright 2020 KMEE
# @author Luis Felipe Mileo <mileo@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class BankPaymentLine(models.Model):
    _inherit = "bank.payment.line"

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

        if payment_mode_id.boleto_discount_perc:
            linhas_pagamentos["cod_desconto"] = "1"

    def prepare_bank_payment_line(self, bank_name_brcobranca):
        payment_mode_id = self.order_id.payment_mode_id
        linhas_pagamentos = self._prepare_boleto_bank_line_vals()
        try:
            bank_method = getattr(
                self, "_prepare_bank_line_{}".format(bank_name_brcobranca.name)
            )
            if bank_method:
                bank_method(payment_mode_id, linhas_pagamentos)
        except Exception:
            pass

        # Cada Banco pode possuir seus Codigos de Instrução
        if (
            self.mov_instruction_code_id.code
            == payment_mode_id.cnab_sending_code_id.code
        ):
            if payment_mode_id.boleto_fee_perc:
                linhas_pagamentos["codigo_multa"] = payment_mode_id.boleto_fee_code
                linhas_pagamentos["percentual_multa"] = payment_mode_id.boleto_fee_perc

            precision = self.env["decimal.precision"]
            precision_account = precision.precision_get("Account")
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
                    linhas_pagamentos["valor_mora"] = round(
                        self.amount_currency
                        * ((payment_mode_id.boleto_interest_perc / 100) / 30),
                        precision_account,
                    )
                if payment_mode_id.boleto_interest_code == "2":
                    linhas_pagamentos[
                        "valor_mora"
                    ] = payment_mode_id.boleto_interest_perc

            if payment_mode_id.boleto_discount_perc:
                linhas_pagamentos["data_desconto"] = self.date.strftime("%Y/%m/%d")
                linhas_pagamentos["valor_desconto"] = round(
                    self.amount_currency * (payment_mode_id.boleto_discount_perc / 100),
                    precision_account,
                )

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
