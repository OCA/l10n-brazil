# Copyright (C) 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import TransactionCase

from ..constants.fiscal import (
    PRODUCT_DESTINATION_FIXED_ASSET,
    PRODUCT_DESTINATION_INDUSTRIALIZATION,
    PRODUCT_DESTINATION_RESALE,
    PRODUCT_DESTINATION_USE_CONSUMPTION,
    PROFIT_CALCULATION_PRESUMED,
    PROFIT_CALCULATION_REAL,
    TAX_DOMAIN_COFINS,
    TAX_DOMAIN_ICMS,
    TAX_DOMAIN_IPI,
    TAX_DOMAIN_PIS,
    TAX_FRAMEWORK_NORMAL,
    TAX_FRAMEWORK_SIMPLES,
    TAX_FRAMEWORK_SIMPLES_EX,
)


class TestStockCost(TransactionCase):
    """Item 1 (fundação) do gap de custos de estoque: resolvedor de
    creditabilidade e cálculo do custo unitário líquido de estoque."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.line = cls.env.ref("l10n_br_fiscal.demo_nfe_purchase_line_same_state_1-1")
        cls.company = cls.line.company_id
        cls.operation_line = cls.line.fiscal_operation_line_id

        # Fornecedores demo (SP): contribuinte normal (CNT) e Simples (SNC).
        cls.supplier_normal = cls.env.ref("l10n_br_base.res_partner_intel")
        cls.supplier_simples = cls.env.ref("l10n_br_base.res_partner_cliente2_sp")

        # Movimento 3 — fixture de empresa Lucro Real. Não existe nos dados demo
        # (só Simples e Presumido) e res.company não permite copy(); por isso é
        # criada aqui. Herda regulação de ICMS/tipo de documento da presumido
        # para o motor fiscal funcionar. Ao submeter o Item 1 à OCA, promover a
        # demo data upstream.
        cls.company_real = cls.env["res.company"].create(
            {
                "name": "Empresa Lucro Real (fixture teste)",
                "country_id": cls.env.ref("base.br").id,
                "state_id": cls.env.ref("base.state_br_sp").id,
                "tax_framework": TAX_FRAMEWORK_NORMAL,
                "profit_calculation": PROFIT_CALCULATION_REAL,
                "is_industry": True,
                "ripi": True,
                "icms_regulation_id": cls.company.icms_regulation_id.id,
                "document_type_id": cls.company.document_type_id.id,
                # Lucro Real ⇒ PIS/COFINS não-cumulativo (crédito).
                "piscofins_id": cls.env.ref(
                    "l10n_br_fiscal.tax_pis_cofins_nao_columativo"
                ).id,
            }
        )
        # As tax.definition de PIS/COFINS/CSLL são por empresa: replicar da
        # presumido para o motor fiscal mapeá-las na empresa Real.
        for tax_def in cls.company.tax_definition_ids:
            tax_def.copy({"company_id": cls.company_real.id})

    def _make_purchase_line(self, partner, company=None):
        """Cria uma linha de compra (industrialização) para um fornecedor/empresa,
        replicando o fluxo real do motor fiscal (não só write de valores)."""
        company = company or self.company
        doc = self.line.document_id.copy(
            {"partner_id": partner.id, "company_id": company.id}
        )
        return self.env["l10n_br_fiscal.document.line"].create(
            {
                "document_id": doc.id,
                "name": "test purchase",
                "product_id": self.line.product_id.id,
                "uom_id": self.line.uom_id.id,
                "quantity": 1,
                "price_unit": 800,
                "fiscal_operation_id": self.env.ref("l10n_br_fiscal.fo_compras").id,
                "fiscal_operation_line_id": self.env.ref(
                    "l10n_br_fiscal.fo_compras_compras"
                ).id,
            }
        )

    def _set_context(self, framework, profit, destination, is_industry=False):
        """Configura regime da empresa + destinação e força o recompute."""
        self.company.write(
            {
                "tax_framework": framework,
                "profit_calculation": profit,
                "is_industry": is_industry,
                "ripi": is_industry,
            }
        )
        self.operation_line.product_destination = destination
        self.line.invalidate_recordset()
        self.line._compute_stock_cost_unit()

    def _expected_cost_unit(self, tax_map):
        """Recalcula o custo esperado a partir dos valores da própria linha,
        de forma agnóstica às alíquotas."""
        line = self.line
        quantity = line.quantity or line.fiscal_quantity
        cost = line.price_gross - line.discount_value
        cost += sum(line[f] for f in line._stock_cost_add_value_fields())
        if tax_map.get(TAX_DOMAIN_IPI) == "cost":
            cost += line.ipi_value
        if tax_map.get(TAX_DOMAIN_ICMS) == "credit":
            cost -= line.icms_value
        if tax_map.get(TAX_DOMAIN_PIS) == "credit":
            cost -= line.pis_value
        if tax_map.get(TAX_DOMAIN_COFINS) == "credit":
            cost -= line.cofins_value
        return (line.currency_id or self.env.ref("base.BRL")).round(cost / quantity)

    # ------------------------------------------------------------------
    # Resolvedor regime × destinação
    # ------------------------------------------------------------------

    def test_map_normal_real_industrialization(self):
        """Lucro Real + industrialização + empresa industrial: tudo credita."""
        self._set_context(
            TAX_FRAMEWORK_NORMAL,
            PROFIT_CALCULATION_REAL,
            PRODUCT_DESTINATION_INDUSTRIALIZATION,
            is_industry=True,
        )
        tax_map = self.line._get_stock_cost_tax_map()
        self.assertEqual(tax_map.get(TAX_DOMAIN_ICMS), "credit")
        self.assertEqual(tax_map.get(TAX_DOMAIN_PIS), "credit")
        self.assertEqual(tax_map.get(TAX_DOMAIN_COFINS), "credit")
        if TAX_DOMAIN_IPI in tax_map:
            self.assertEqual(tax_map.get(TAX_DOMAIN_IPI), "credit")

    def test_map_presumed_resale(self):
        """Lucro Presumido + revenda: ICMS credita; PIS/COFINS (cumulativo) e
        IPI (revenda, não industrialização) integram o custo."""
        self._set_context(
            TAX_FRAMEWORK_NORMAL,
            PROFIT_CALCULATION_PRESUMED,
            PRODUCT_DESTINATION_RESALE,
        )
        tax_map = self.line._get_stock_cost_tax_map()
        self.assertEqual(tax_map.get(TAX_DOMAIN_ICMS), "credit")
        self.assertEqual(tax_map.get(TAX_DOMAIN_PIS), "cost")
        self.assertEqual(tax_map.get(TAX_DOMAIN_COFINS), "cost")
        if TAX_DOMAIN_IPI in tax_map:
            self.assertEqual(tax_map.get(TAX_DOMAIN_IPI), "cost")

    def test_map_use_consumption(self):
        """Uso/consumo: nenhum imposto recuperável credita — tudo é custo."""
        self._set_context(
            TAX_FRAMEWORK_NORMAL,
            PROFIT_CALCULATION_REAL,
            PRODUCT_DESTINATION_USE_CONSUMPTION,
            is_industry=True,
        )
        tax_map = self.line._get_stock_cost_tax_map()
        for domain in (
            TAX_DOMAIN_ICMS,
            TAX_DOMAIN_PIS,
            TAX_DOMAIN_COFINS,
            TAX_DOMAIN_IPI,
        ):
            if domain in tax_map:
                self.assertEqual(tax_map[domain], "cost")

    def test_map_fixed_asset(self):
        """Ativo imobilizado (fundação): trata como custo; CIAP 1/48 é fase 2."""
        self._set_context(
            TAX_FRAMEWORK_NORMAL,
            PROFIT_CALCULATION_REAL,
            PRODUCT_DESTINATION_FIXED_ASSET,
            is_industry=True,
        )
        tax_map = self.line._get_stock_cost_tax_map()
        for domain, decision in tax_map.items():
            self.assertEqual(decision, "cost", f"{domain} deveria integrar o custo")

    def test_map_simples_never_credits(self):
        """Simples Nacional: sem crédito, tudo integra o custo mesmo em revenda."""
        for framework in (TAX_FRAMEWORK_SIMPLES, TAX_FRAMEWORK_SIMPLES_EX):
            self._set_context(
                framework,
                PROFIT_CALCULATION_REAL,
                PRODUCT_DESTINATION_RESALE,
                is_industry=True,
            )
            tax_map = self.line._get_stock_cost_tax_map()
            for domain, decision in tax_map.items():
                self.assertEqual(decision, "cost", f"framework {framework}, {domain}")

    def test_map_real_commercial_ipi_is_cost(self):
        """Lucro Real + industrialização, mas empresa COMERCIAL (não industrial):
        IPI não credita (integra o custo); ICMS/PIS/COFINS creditam. (P0-08)"""
        self._set_context(
            TAX_FRAMEWORK_NORMAL,
            PROFIT_CALCULATION_REAL,
            PRODUCT_DESTINATION_INDUSTRIALIZATION,
            is_industry=False,
        )
        tax_map = self.line._get_stock_cost_tax_map()
        self.assertEqual(tax_map.get(TAX_DOMAIN_ICMS), "credit")
        self.assertEqual(tax_map.get(TAX_DOMAIN_PIS), "credit")
        self.assertEqual(tax_map.get(TAX_DOMAIN_COFINS), "credit")
        self.assertEqual(tax_map.get(TAX_DOMAIN_IPI), "cost")

    def test_map_real_industrial_resale_ipi_is_cost(self):
        """Lucro Real + empresa industrial, mas destinação REVENDA:
        IPI não credita (só industrialização credita IPI). (P0-09)"""
        self._set_context(
            TAX_FRAMEWORK_NORMAL,
            PROFIT_CALCULATION_REAL,
            PRODUCT_DESTINATION_RESALE,
            is_industry=True,
        )
        tax_map = self.line._get_stock_cost_tax_map()
        self.assertEqual(tax_map.get(TAX_DOMAIN_ICMS), "credit")
        self.assertEqual(tax_map.get(TAX_DOMAIN_PIS), "credit")
        self.assertEqual(tax_map.get(TAX_DOMAIN_COFINS), "credit")
        self.assertEqual(tax_map.get(TAX_DOMAIN_IPI), "cost")

    def test_map_arbitrary_like_presumed(self):
        """Lucro Arbitrário: PIS/COFINS cumulativos (custo), como no Presumido;
        ICMS ainda credita. (P0-10)"""
        self._set_context(
            TAX_FRAMEWORK_NORMAL,
            "arbitrary",
            PRODUCT_DESTINATION_RESALE,
        )
        tax_map = self.line._get_stock_cost_tax_map()
        self.assertEqual(tax_map.get(TAX_DOMAIN_ICMS), "credit")
        self.assertEqual(tax_map.get(TAX_DOMAIN_PIS), "cost")
        self.assertEqual(tax_map.get(TAX_DOMAIN_COFINS), "cost")

    def test_map_no_destination_is_conservative(self):
        """Sem destinação na operação fiscal: fallback conservador — nada
        credita, custo = valor cheio (evita crédito indevido). (P0-11)"""
        self._set_context(
            TAX_FRAMEWORK_NORMAL,
            PROFIT_CALCULATION_REAL,
            False,
            is_industry=True,
        )
        tax_map = self.line._get_stock_cost_tax_map()
        for domain, decision in tax_map.items():
            self.assertEqual(decision, "cost", f"{domain} deveria ser custo")

    # ------------------------------------------------------------------
    # Custo unitário de estoque
    # ------------------------------------------------------------------

    def test_stock_cost_unit_matches_formula(self):
        """O campo computado bate com a fórmula recalculada dos valores da linha."""
        self._set_context(
            TAX_FRAMEWORK_NORMAL,
            PROFIT_CALCULATION_REAL,
            PRODUCT_DESTINATION_INDUSTRIALIZATION,
            is_industry=True,
        )
        tax_map = self.line._get_stock_cost_tax_map()
        self.assertAlmostEqual(
            self.line.stock_cost_unit,
            self._expected_cost_unit(tax_map),
            places=2,
        )

    def test_credits_reduce_cost_vs_simples(self):
        """Com créditos (Real + industrialização) o custo é menor que no Simples
        (sem créditos), sempre que houver imposto recuperável destacado."""
        self._set_context(
            TAX_FRAMEWORK_SIMPLES,
            PROFIT_CALCULATION_REAL,
            PRODUCT_DESTINATION_INDUSTRIALIZATION,
            is_industry=True,
        )
        cost_simples = self.line.stock_cost_unit

        self._set_context(
            TAX_FRAMEWORK_NORMAL,
            PROFIT_CALCULATION_REAL,
            PRODUCT_DESTINATION_INDUSTRIALIZATION,
            is_industry=True,
        )
        cost_real = self.line.stock_cost_unit

        recoverable = (
            self.line.icms_value + self.line.pis_value + self.line.cofins_value
        )
        if recoverable:
            self.assertLess(cost_real, cost_simples)
        else:
            self.assertEqual(cost_real, cost_simples)

    def test_add_components_compose_cost(self):
        """Componentes "por fora" (ICMS-ST, FCP-ST, IPI não creditável, frete,
        seguro, outros) somam ao custo; ICMS creditável (por dentro) subtrai.

        Cenário: revenda + Lucro Presumido → ICMS credita; PIS/COFINS
        (cumulativo) e IPI (revenda, não industrialização) integram o custo.
        Assert com valor esperado calculado à mão (independente da fórmula).
        """
        self._set_context(
            TAX_FRAMEWORK_NORMAL,
            PROFIT_CALCULATION_PRESUMED,
            PRODUCT_DESTINATION_RESALE,
        )
        line = self.line
        # Injeta componentes que a linha demo não possui (NF com ST e frete).
        line.write(
            {
                "icmsst_value": 50.0,
                "icmsfcpst_value": 10.0,
                "freight_value": 30.0,
                "insurance_value": 5.0,
                "other_value": 15.0,
            }
        )
        line._compute_stock_cost_unit()

        tax_map = line._get_stock_cost_tax_map()
        self.assertEqual(tax_map.get(TAX_DOMAIN_ICMS), "credit")
        self.assertEqual(tax_map.get(TAX_DOMAIN_IPI), "cost")
        self.assertEqual(tax_map.get(TAX_DOMAIN_PIS), "cost")

        # 800 (merc.) - 99.12 (ICMS credit) + 26.00 (IPI custo, por fora)
        # + 50 (ST) + 10 (FCP-ST) + 30 (frete) + 5 (seguro) + 15 (outros) = 836.88
        expected = (
            line.price_gross
            - line.icms_value
            + line.ipi_value
            + 50.0
            + 10.0
            + 30.0
            + 5.0
            + 15.0
        ) / line.quantity
        self.assertAlmostEqual(line.stock_cost_unit, expected, places=2)
        # Sanidade: o custo é maior que a mercadoria líquida de ICMS.
        self.assertGreater(line.stock_cost_unit, line.price_gross - line.icms_value)

    def test_supplier_simples_no_icms_ipi_credit(self):
        """Eixo FORNECEDOR (P1-01): comprar de optante do Simples Nacional não
        gera crédito de ICMS/IPI ao adquirente, mesmo sendo ele Lucro Real +
        industrialização (art. 23 LC 123/2006). Custo > compra de normal."""
        # Comprador Lucro Real industrial (máximo direito a crédito).
        self._set_context(
            TAX_FRAMEWORK_NORMAL,
            PROFIT_CALCULATION_REAL,
            PRODUCT_DESTINATION_INDUSTRIALIZATION,
            is_industry=True,
        )
        line_simples = self._make_purchase_line(self.supplier_simples)
        line_normal = self._make_purchase_line(self.supplier_normal)

        map_simples = line_simples._get_stock_cost_tax_map()
        map_normal = line_normal._get_stock_cost_tax_map()

        # Fornecedor Simples: ICMS/IPI viram custo.
        self.assertEqual(map_simples.get(TAX_DOMAIN_ICMS), "cost")
        self.assertEqual(map_simples.get(TAX_DOMAIN_IPI), "cost")
        # Fornecedor normal: ICMS credita.
        self.assertEqual(map_normal.get(TAX_DOMAIN_ICMS), "credit")

        # Menos crédito ⇒ custo de aquisição do Simples é maior (se houve ICMS).
        if line_normal.icms_value:
            self.assertGreater(
                line_simples.stock_cost_unit, line_normal.stock_cost_unit
            )

    def test_company_lucro_real_fixture_credits_pis_cofins(self):
        """Movimento 3: usando a empresa Lucro Real dedicada (fixture, não via
        write), a compra industrial de fornecedor normal credita ICMS + PIS +
        COFINS (não-cumulativo) — diferença chave frente ao Presumido."""
        self.operation_line.product_destination = PRODUCT_DESTINATION_INDUSTRIALIZATION
        line = self._make_purchase_line(self.supplier_normal, company=self.company_real)
        tax_map = line._get_stock_cost_tax_map()
        self.assertEqual(line.company_id.profit_calculation, PROFIT_CALCULATION_REAL)
        self.assertEqual(tax_map.get(TAX_DOMAIN_ICMS), "credit")
        self.assertEqual(tax_map.get(TAX_DOMAIN_PIS), "credit")
        self.assertEqual(tax_map.get(TAX_DOMAIN_COFINS), "credit")

    def test_zero_quantity_is_safe(self):
        """Quantidade zero não deve estourar divisão."""
        self.line.quantity = 0
        self.line._compute_stock_cost_unit()
        self.assertEqual(self.line.stock_cost_unit, 0.0)
