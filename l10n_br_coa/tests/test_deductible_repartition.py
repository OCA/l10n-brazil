# Copyright (C) 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
"""Contas das linhas de repartição dos impostos dedutiveis.

Na entrada, o imposto dedutivel nao e deducao de receita: ele sai do custo da
propria linha. Sem conta na linha de repartição o core cai na conta da linha
base - estoque, conta ponte ou despesa - que e a mesma convencao do
`total_void` do `account.tax`.

Na saida a conta de deducao de receita continua correta, e o teste protege
esse lado de uma correcao ampla demais.
"""

from odoo.tests import TransactionCase


class TestDeductibleRepartition(TransactionCase):
    def _tax_repartition(self, taxes):
        return (
            taxes.invoice_repartition_line_ids | taxes.refund_repartition_line_ids
        ).filtered(lambda line: line.repartition_type == "tax")

    def test_purchase_deductible_taxes_have_no_account(self):
        """Imposto dedutivel de entrada cai na conta da linha base."""
        taxes = self.env["account.tax"].search(
            [
                ("deductible", "=", True),
                ("type_tax_use", "=", "purchase"),
                "|",
                ("active", "=", True),
                ("active", "=", False),
            ]
        )
        if not taxes:
            self.skipTest("Nenhum imposto dedutivel de compra nesta base.")
        with_account = self._tax_repartition(taxes).filtered("account_id")
        self.assertFalse(
            with_account,
            "Impostos dedutiveis de entrada com conta na linha de repartição: "
            "%s. Com conta propria o credito vira um espelho decorativo - a "
            "fatura debita a conta a compensar e credita outra conta, sem "
            "tirar o imposto do custo da mercadoria."
            % ", ".join(sorted(set(with_account.mapped("tax_id.display_name")))),
        )

    def test_sale_deductible_taxes_keep_their_account(self):
        """Na saida a conta de deducao de receita continua sendo usada.

        Nem todo imposto dedutivel de saida tem conta: IBS, CBS e IS nunca
        tiveram `ded_account_id` no plano. O que o teste protege e que a
        correcao da entrada nao alcance os que tem - o ICMS de saida e a
        testemunha, porque e o par direto do imposto de entrada corrigido.
        """
        # `description` vem da coluna homonima do account.tax.template e nao
        # e traduzida. O caminho pelo grupo fiscal exigiria o l10n_br_account,
        # que este modulo nao conhece.
        icms_out = self.env["account.tax"].search(
            [
                ("deductible", "=", True),
                ("type_tax_use", "=", "sale"),
                ("description", "=", "ICMS"),
            ],
            limit=1,
        )
        if not icms_out:
            self.skipTest("Nenhum ICMS dedutivel de saida nesta base.")
        repartition = icms_out.invoice_repartition_line_ids.filtered(
            lambda line: line.repartition_type == "tax"
        )
        self.assertTrue(
            repartition.account_id,
            "O %s ficou sem conta na linha de repartição. Na saida o imposto "
            "dedutivel e deducao de receita bruta e a conta esta correta: a "
            "correcao aplicada a entrada nao pode alcancar este lado."
            % icms_out.display_name,
        )

    def test_deductible_factor_is_applied_without_account(self):
        """O fator vale mesmo sem conta, inclusive na devolução.

        `_update_repartition_lines` so aplicava o fator quando havia conta, e
        um dedutivel sem conta de devolução ficava com +100 - invertendo o
        sinal na nota de credito.
        """
        taxes = self.env["account.tax"].search(
            [
                ("deductible", "=", True),
                ("type_tax_use", "=", "purchase"),
                "|",
                ("active", "=", True),
                ("active", "=", False),
            ]
        )
        if not taxes:
            self.skipTest("Nenhum imposto dedutivel de compra nesta base.")
        wrong = self._tax_repartition(taxes).filtered(
            lambda line: line.factor_percent != -100
        )
        self.assertFalse(
            wrong,
            "Linhas de repartição de imposto dedutivel com fator diferente de "
            "-100: %s."
            % ", ".join(
                "%s (%s)" % (line.tax_id.display_name, line.factor_percent)
                for line in wrong
            ),
        )
