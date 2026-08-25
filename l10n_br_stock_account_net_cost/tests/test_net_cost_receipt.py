# Copyright (C) 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
"""O recebimento nasce pelo custo liquido.

Este modulo cuida so do momento da valoracao: adiantar para o recebimento o
custo que a fatura garantiria de qualquer forma. O ciclo contabil completo -
pedido, recebimento, fatura, confirmacao - e coberto em
`l10n_br_purchase_stock/tests/test_net_acquisition_cost.py`, porque depende do
modulo de compras, que este aqui nao exige.

Os cenarios validam o recebimento de verdade em vez de chamar
`_get_price_unit()` direto: o metodo so age sobre movimentacoes de entrada
(`_is_in()`), e isso depende de linhas de movimento que so existem depois da
reserva. Afirmar sobre a camada de valoracao resultante e o que corresponde ao
que acontece em producao.
"""

import unittest

from odoo.tests import TransactionCase

SIMPLES_FRAMEWORKS = ("1", "4")


class TestNetCostReceipt(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.ref(
            "l10n_br_base.empresa_lucro_presumido", raise_if_not_found=False
        )
        if not cls.company:
            raise unittest.SkipTest("Requer os dados de demonstracao do l10n_br_base.")
        cls.env.user.company_ids += cls.company
        cls.env.user.company_id = cls.company

        cls.supplier = cls.env.ref("l10n_br_base.res_partner_intel")
        if cls.supplier.tax_framework in SIMPLES_FRAMEWORKS:
            raise unittest.SkipTest(
                "Fornecedor do Simples nao transfere credito de ICMS "
                "(LC 123/2006, art. 23)."
            )

        cls.fiscal_operation = cls.env.ref("l10n_br_fiscal.fo_compras")
        cls.fiscal_operation_line = cls.env.ref("l10n_br_fiscal.fo_compras_compras")
        cls.warehouse = cls.env["stock.warehouse"].search(
            [("company_id", "=", cls.company.id)], limit=1
        )
        if not cls.warehouse:
            raise unittest.SkipTest("Nenhum armazem na empresa.")

        # AVCO com inventario periodico: basta para a camada de valoracao
        # guardar o custo, sem exigir plano de contas nesta suite. O custo
        # padrao ignoraria o preco da movimentacao.
        category = (
            cls.env["product.category"]
            .with_company(cls.company)
            .create(
                {
                    "name": "Custo Liquido no Recebimento (AVCO)",
                    "property_cost_method": "average",
                    "property_valuation": "manual_periodic",
                }
            )
        )
        cls.product = (
            cls.env.ref("product.product_product_12")
            .with_company(cls.company)
            .copy(
                {
                    "name": "Produto Custo Liquido no Recebimento",
                    "default_code": "TEST-NET-COST-IN",
                    "categ_id": category.id,
                    "detailed_type": "product",
                    "standard_price": 0.0,
                    "seller_ids": [(5, 0, 0)],
                }
            )
        )

    def _receive(self, price=100.0, qty=1.0, with_operation=True):
        """Cria e valida um recebimento, devolvendo a movimentacao."""
        picking_vals = {
            "picking_type_id": self.warehouse.in_type_id.id,
            "partner_id": self.supplier.id,
            "location_id": self.env.ref("stock.stock_location_suppliers").id,
            "location_dest_id": self.warehouse.lot_stock_id.id,
            "company_id": self.company.id,
        }
        move_vals = {
            "name": self.product.name,
            "product_id": self.product.id,
            "product_uom": self.product.uom_id.id,
            "product_uom_qty": qty,
            "price_unit": price,
            "location_id": picking_vals["location_id"],
            "location_dest_id": picking_vals["location_dest_id"],
            "company_id": self.company.id,
            "partner_id": self.supplier.id,
        }
        if with_operation:
            picking_vals["fiscal_operation_id"] = self.fiscal_operation.id
            move_vals["fiscal_operation_id"] = self.fiscal_operation.id
            move_vals["fiscal_operation_line_id"] = self.fiscal_operation_line.id
        picking = (
            self.env["stock.picking"].with_company(self.company).create(picking_vals)
        )
        move_vals["picking_id"] = picking.id
        move = self.env["stock.move"].with_company(self.company).create(move_vals)
        picking.action_confirm()
        picking.action_assign()
        move.quantity_done = qty
        picking.button_validate()
        return move

    def test_receipt_layer_is_net_of_creditable_taxes(self):
        """A camada de valoracao nasce sem o imposto que sera creditado."""
        move = self._receive(price=100.0)
        creditable = move._get_creditable_tax_value()
        self.assertGreater(
            creditable,
            0.0,
            "Nenhum imposto creditavel na movimentacao: o cenario nao testa "
            "nada. Confira se os impostos de entrada tem conta na linha de "
            "repartição.",
        )
        layer = move.stock_valuation_layer_ids
        self.assertTrue(layer, "O recebimento nao gerou camada de valoracao.")
        expected = move._get_net_cost_price_unit()
        self.assertAlmostEqual(
            layer.unit_cost,
            expected,
            places=2,
            msg="A camada guardou %.2f, esperado %.2f (bruto %.2f menos %.2f "
            "de imposto creditavel, mais impostos por fora)."
            % (layer.unit_cost, expected, move.price_unit, creditable),
        )
        self.assertLess(
            layer.unit_cost,
            move.price_unit,
            "O custo da camada nao ficou abaixo do preco bruto: o imposto "
            "creditavel continuou no custo.",
        )

    def test_creditability_comes_from_the_chart_of_accounts(self):
        """Imposto sem conta na linha de repartição continua no custo.

        Nenhuma lista de CST e nenhuma regra de regime em codigo: quem decide
        e a existencia de conta de credito, a mesma convencao que o core usa
        em `total_void`.
        """
        before = self._receive(price=100.0)._get_creditable_tax_value()
        icms = (
            self.env["account.tax"]
            .search(
                [
                    ("type_tax_use", "=", "purchase"),
                    ("deductible", "=", False),
                    ("company_id", "=", self.company.id),
                    ("tax_group_id.fiscal_tax_group_id.tax_domain", "=", "icms"),
                ],
                limit=1,
            )
            .invoice_repartition_line_ids.filtered(
                lambda line: line.repartition_type == "tax"
            )
        )
        if not icms or not icms.account_id:
            self.skipTest("ICMS de entrada sem conta de credito nesta base.")
        icms.account_id = False

        after_move = self._receive(price=100.0)
        self.assertLess(
            after_move._get_creditable_tax_value(),
            before,
            "Tirar a conta de credito do ICMS tinha que remove-lo do total "
            "creditavel.",
        )
        self.assertGreater(
            after_move.stock_valuation_layer_ids.unit_cost,
            0.0,
            "A camada ficou sem custo.",
        )

    def test_move_without_fiscal_operation_line_keeps_default(self):
        """Sem linha de operacao fiscal nao ha como saber o tratamento.

        O custo liquido fica por conta da fatura, que e quem sempre tem a
        informacao fiscal.
        """
        move = self._receive(price=100.0, with_operation=False)
        self.assertFalse(move._net_cost_applies())
        self.assertAlmostEqual(
            move.stock_valuation_layer_ids.unit_cost, 100.0, places=2
        )
