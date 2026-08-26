# Copyright 2026 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
"""Cenarios de compra com impostos creditaveis.

Cada teste roda o ciclo completo - pedido, recebimento, fatura e
**confirmacao da fatura** - e afirma sobre invariantes contabeis, nunca sobre
o motor de custo. Ver README.md para o que cada invariante prova.
"""

from .common import TestCreditabilityCommon


class TestPurchaseCreditability(TestCreditabilityCommon):
    def _core_checks(self, result):
        """I1 a I4: os invariantes que valem em qualquer estrategia."""
        delta = result.delta
        return [
            ("I1 ponte 1.1.9.0.01 (delta do ciclo)", 0.0, delta["bridge"]),
            ("I2 camada de valoracao SVL (delta)", result.bill_net, delta["svl"]),
            ("I2 estoque 1.1.3.1.02 (delta)", result.bill_net, delta["stock"]),
            (
                "I3 a compensar 1.1.4.1.* (delta)",
                result.bill_recoverable,
                delta["recoverable"],
            ),
            ("I4 CMV 5.1.1.1.01 (delta)", 0.0, delta["cogs"]),
        ]

    # ------------------------------------------------------------------

    def test_cycle_deductible_off(self):
        """Dedutiveis desligados - o default de fabrica da operacao Compras.

        E o cenario que hoje deixa o valor do credito pendurado na conta
        ponte e o estoque valorizado pelo bruto.
        """
        self._set_deductible_taxes(False)
        result = self._run_cycle(price=100.0)
        self.check_ledger(
            "dedutiveis OFF . pedido 100,00 . fatura 100,00",
            self._core_checks(result),
            result,
        )

    def test_cycle_deductible_on(self):
        """Dedutiveis ligados - o imposto aparece em duas linhas na fatura.

        Os saldos tem que ser os mesmos do cenario OFF: a flag muda a
        apresentacao, nao o resultado.
        """
        self._set_deductible_taxes(True)
        result = self._run_cycle(price=100.0)
        self.check_ledger(
            "dedutiveis ON . pedido 100,00 . fatura 100,00",
            self._core_checks(result),
            result,
        )

    def test_on_off_converge(self):
        """I6: ligar ou desligar dedutiveis nao pode mudar saldo nenhum."""
        self._set_deductible_taxes(False)
        off = self._run_cycle(price=100.0)
        self._set_deductible_taxes(True)
        on = self._run_cycle(price=100.0)
        self.check_ledger(
            "convergencia ON vs OFF . preco 100,00 (esperado = OFF, obtido = ON)",
            [
                ("I6 ponte", off.delta["bridge"], on.delta["bridge"]),
                ("I6 estoque", off.delta["stock"], on.delta["stock"]),
                ("I6 camada de valoracao SVL", off.delta["svl"], on.delta["svl"]),
                ("I6 a compensar", off.delta["recoverable"], on.delta["recoverable"]),
                ("I6 liquido na conta da linha", off.bill_net, on.bill_net),
            ],
            on,
        )

    def test_real_price_difference(self):
        """I5: o passo 3 continua absorvendo diferenca real de preco.

        Pedido a 100, fatura a 110. A correcao tem que ser a diferenca
        liquida entre os dois, e nunca o valor do imposto creditavel - que e
        exatamente o que ele lanca errado hoje.
        """
        self._set_deductible_taxes(False)
        result = self._run_cycle(price=100.0, bill_price=110.0)
        expected_correction = round(result.bill_net - result.receipt_value, 2)
        self.check_ledger(
            "diferenca real de preco . pedido 100,00 . fatura 110,00",
            [
                ("I1 ponte 1.1.9.0.01 (delta do ciclo)", 0.0, result.delta["bridge"]),
                (
                    "I2 camada de valoracao SVL (delta)",
                    result.bill_net,
                    result.delta["svl"],
                ),
                ("I5 correcao do passo 3", expected_correction, result.pdiff_value),
            ],
            result,
        )
        self.assertNotAlmostEqual(
            abs(result.pdiff_value),
            abs(result.bill_recoverable),
            places=2,
            msg=(
                f"O passo 3 lancou {result.pdiff_value:.2f}, que e o valor dos "
                f"impostos creditaveis ({result.bill_recoverable:.2f}), e nao a "
                "diferenca real de preco entre o pedido e a fatura. E o sintoma "
                "de a base da comparacao ser o preco bruto."
            ),
        )

    def test_tax_without_account_stays_in_cost(self):
        """Quem decide creditabilidade e o plano de contas.

        Tirando a conta da linha de repartição do ICMS Entrada, o imposto
        passa a cair na conta da linha base e tem que continuar no custo -
        mesma convencao do `total_void` do core. Os invariantes contabeis
        continuam valendo, so muda o valor liquido.
        """
        self._set_deductible_taxes(False)
        icms = self.env["account.tax"].search(
            [
                ("type_tax_use", "=", "purchase"),
                ("deductible", "=", False),
                ("company_id", "=", self.company.id),
                ("tax_group_id.fiscal_tax_group_id.tax_domain", "=", "icms"),
            ],
            limit=1,
        )
        self.assertTrue(icms, "Nao encontrei o imposto contabil de ICMS de entrada.")
        repartition = icms.invoice_repartition_line_ids.filtered(
            lambda line: line.repartition_type == "tax"
        )
        self.assertTrue(
            repartition.account_id,
            "O ICMS Entrada ja estava sem conta: o cenario nao testa nada.",
        )
        repartition.account_id = False

        result = self._run_cycle(price=100.0)
        checks = self._core_checks(result)
        checks.append(
            (
                "ICMS fora do credito (a compensar sem ICMS)",
                result.bill_recoverable,
                result.delta["recoverable"],
            )
        )
        self.check_ledger(
            "ICMS sem conta na repartição . dedutiveis OFF . preco 100,00",
            checks,
            result,
        )

    def test_bill_via_picking_wizard(self):
        """Faturando pelo assistente do picking, e nao pelo pedido.

        A premissa de que essa rota perderia o `purchase_line_id` - e com ele o
        passo 3, que so age sobre linhas ligadas a uma linha de pedido via
        `_get_valued_in_moves()` - **nao se confirma**: o l10n_br_purchase_stock
        mantem a ligacao. O teste fixa isso, porque se um dia a ligacao se
        perder o custo passa a ficar bruto em silencio.

        O buraco de verdade fica na fatura sem pedido nenhum (entrada de NF-e
        avulsa), que nao esta coberta aqui.
        """
        self._set_deductible_taxes(False)
        result = self._run_cycle(price=100.0, via_wizard=True)
        product_lines = result.bill.invoice_line_ids.filtered(
            lambda line: line.display_type == "product"
        )
        self.assertTrue(
            product_lines.purchase_line_id,
            "A fatura gerada pelo assistente do picking perdeu a ligacao com a "
            "linha do pedido. Sem `purchase_line_id` o passo 3 nao roda e "
            "nenhuma estrategia de custo liquido corrige o custo.",
        )
        self.check_ledger(
            "fatura pelo assistente do picking . dedutiveis OFF . preco 100,00",
            self._core_checks(result),
            result,
        )
