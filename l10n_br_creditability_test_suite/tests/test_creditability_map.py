# Copyright 2026 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
"""Os quatro casos do mapa de testes.

Duas operacoes x dois modos de `deductible_taxes`:

    CASO 1A  CFOP 1102  revenda         dedutiveis OFF
    CASO 1B  CFOP 1102  revenda         dedutiveis ON
    CASO 2A  CFOP 1556  uso e consumo   dedutiveis OFF
    CASO 2B  CFOP 1556  uso e consumo   dedutiveis ON

O eixo das operacoes existe por causa da **creditabilidade condicional**. Numa
compra para revenda o ICMS destacado gera credito, abatido do ICMS devido na
saida (LC 87/96, art. 20): o imposto nunca foi custo, e um ativo a recuperar, e
o estoque vale o preco menos o ICMS.

Numa compra para uso e consumo quem compra e consumidor final - nao havera
saida tributada onde abater. O credito de ICMS sobre material de uso e consumo
segue vedado ate 2033 (LC 87/96, art. 33, I, na redacao da LC 171/2019). O
imposto e custo, e o estoque vale o preco cheio.

O eixo do `deductible_taxes` nao muda quanto se credita: muda so **por qual
mecanismo** o imposto sai do valor da linha. Desligado, o abatimento ja vem
embutido no valor da linha de produto; ligado, a linha vai cheia e uma perna de
-100% credita de volta. Os saldos finais deveriam ser iguais nos dois.
"""

from .common import TestCreditabilityCommon

OPERATION_RESALE = "l10n_br_fiscal.fo_compras_compras_comercializacao"
OPERATION_OWN_USE = "l10n_br_fiscal.fo_compras_compras_uso_consumo"


class TestCreditabilityMap(TestCreditabilityCommon):
    def _ledger_checks(self, result):
        """Invariantes contabeis, validos em qualquer operacao."""
        delta = result.delta
        return [
            ("I1 ponte 1.1.9.0.01 (delta do ciclo)", 0.0, delta["bridge"]),
            ("I2 camada de valoracao SVL (delta)", result.bill_net, delta["svl"]),
            ("I2 estoque 1.1.3.1.02 (delta)", result.bill_net, delta["stock"]),
            ("I4 CMV 5.1.1.1.01 (delta)", 0.0, delta["cogs"]),
        ]

    def _run_case(self, operation_xmlid, deductible, label):
        self._set_deductible_taxes(deductible)
        return (
            self._run_cycle(price=100.0, operation_line=self.env.ref(operation_xmlid)),
            label,
        )

    # ------------------------------------------------------------------
    # CASO 1 - compra para revenda: o ICMS credita e sai do custo
    # ------------------------------------------------------------------

    def test_caso_1a_revenda_dedutiveis_off(self):
        result, label = self._run_case(
            OPERATION_RESALE, False, "CASO 1A . CFOP 1102 revenda . dedutiveis OFF"
        )
        checks = self._ledger_checks(result)
        checks.append(
            (
                "ICMS creditado (1.1.4.1.02)",
                result.delta["icms"],
                result.delta["icms"],
            )
        )
        self.assertGreater(
            result.delta["icms"],
            0.0,
            "Numa compra para revenda o ICMS destacado tem que gerar credito "
            "(LC 87/96, art. 20). Nada foi para 1.1.4.1.02 ICMS a Compensar.",
        )
        self.check_ledger(label, checks, result)

    def test_caso_1b_revenda_dedutiveis_on(self):
        result, label = self._run_case(
            OPERATION_RESALE, True, "CASO 1B . CFOP 1102 revenda . dedutiveis ON"
        )
        self.check_ledger(label, self._ledger_checks(result), result)

    # ------------------------------------------------------------------
    # CASO 2 - compra para uso e consumo: o ICMS NAO credita, fica no custo
    # ------------------------------------------------------------------

    def test_caso_2a_uso_consumo_dedutiveis_off(self):
        result, label = self._run_case(
            OPERATION_OWN_USE,
            False,
            "CASO 2A . CFOP 1556 uso e consumo . dedutiveis OFF",
        )
        checks = self._ledger_checks(result)
        checks.append(("ICMS creditado (1.1.4.1.02)", 0.0, result.delta["icms"]))
        self.check_ledger(label, checks, result)
        self.assertAlmostEqual(
            result.delta["icms"],
            0.0,
            places=2,
            msg="Creditabilidade condicional: numa compra para uso e consumo o "
            "ICMS nao gera credito ate 2033 (LC 87/96, art. 33, I, na redacao "
            "da LC 171/2019). Foram para 1.1.4.1.02 ICMS a Compensar %.2f que "
            "deveriam ter ficado no custo do estoque." % result.delta["icms"],
        )

    def test_caso_2b_uso_consumo_dedutiveis_on(self):
        result, label = self._run_case(
            OPERATION_OWN_USE, True, "CASO 2B . CFOP 1556 uso e consumo . dedutiveis ON"
        )
        checks = self._ledger_checks(result)
        checks.append(("ICMS creditado (1.1.4.1.02)", 0.0, result.delta["icms"]))
        self.check_ledger(label, checks, result)
        self.assertAlmostEqual(
            result.delta["icms"],
            0.0,
            places=2,
            msg="Creditabilidade condicional nao observada com dedutiveis "
            "ligados: %.2f foram para ICMS a Compensar numa operacao de uso e "
            "consumo." % result.delta["icms"],
        )

    # ------------------------------------------------------------------
    # O eixo transversal: a flag nao pode mudar saldo
    # ------------------------------------------------------------------

    def test_flag_nao_muda_saldo_em_nenhuma_operacao(self):
        """1A contra 1B, e 2A contra 2B."""
        for operation_xmlid, nome in (
            (OPERATION_RESALE, "revenda CFOP 1102"),
            (OPERATION_OWN_USE, "uso e consumo CFOP 1556"),
        ):
            with self.subTest(operacao=nome):
                self._set_deductible_taxes(False)
                off = self._run_cycle(
                    price=100.0, operation_line=self.env.ref(operation_xmlid)
                )
                self._set_deductible_taxes(True)
                on = self._run_cycle(
                    price=100.0, operation_line=self.env.ref(operation_xmlid)
                )
                self.check_ledger(
                    "%s . A contra B (esperado = OFF, obtido = ON)" % nome,
                    [
                        ("ponte", off.delta["bridge"], on.delta["bridge"]),
                        ("estoque", off.delta["stock"], on.delta["stock"]),
                        ("camada SVL", off.delta["svl"], on.delta["svl"]),
                        (
                            "a compensar",
                            off.delta["recoverable"],
                            on.delta["recoverable"],
                        ),
                        ("liquido na conta da linha", off.bill_net, on.bill_net),
                    ],
                    on,
                )

    # ------------------------------------------------------------------
    # O eixo da operacao: revenda e uso e consumo tem que divergir
    # ------------------------------------------------------------------

    def test_operacao_muda_o_custo_do_estoque(self):
        """A prova da creditabilidade condicional, num teste so.

        Mesmo produto, mesmo preco, mesmo fornecedor. So a operacao muda. O
        estoque de uso e consumo tem que valer **mais**, exatamente o ICMS que
        a revenda credita e ele nao.
        """
        self._set_deductible_taxes(False)
        resale = self._run_cycle(
            price=100.0, operation_line=self.env.ref(OPERATION_RESALE)
        )
        own_use = self._run_cycle(
            price=100.0, operation_line=self.env.ref(OPERATION_OWN_USE)
        )
        self.check_ledger(
            "creditabilidade condicional . revenda contra uso e consumo",
            [
                (
                    "estoque de uso e consumo = estoque de revenda + ICMS",
                    round(resale.delta["svl"] + resale.delta["icms"], 2),
                    own_use.delta["svl"],
                ),
                ("ICMS creditado no uso e consumo", 0.0, own_use.delta["icms"]),
            ],
            own_use,
        )
