# Copyright (C) 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import TransactionCase


class TestStockCostPurchaseOrder(TransactionCase):
    """Fase C1/C2 — custo líquido como ferramenta de decisão de compra:
    o comprador compara fornecedores pelo custo de aquisição REAL (não pelo
    preço de tabela), com indicador de estimativa para compras
    interestaduais (alíquota interestadual na entrada ainda não suportada
    pelo motor — Fase B)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.company = cls.env.ref("l10n_br_base.empresa_lucro_presumido")
        cls.env.user.company_ids += cls.company
        cls.env.user.company_id = cls.company
        cls.product = cls.env.ref("product.product_product_6")
        cls.fiscal_operation = cls.env.ref("l10n_br_fiscal.fo_compras")
        cls.fiscal_operation_line = cls.env.ref("l10n_br_fiscal.fo_compras_compras")
        # Fornecedores: normal SP (mesma UF), Simples SP, normal outra UF.
        cls.supplier_normal_sp = cls.env.ref("l10n_br_base.res_partner_intel")
        cls.supplier_simples_sp = cls.env.ref("l10n_br_base.res_partner_cliente2_sp")
        cls.supplier_other_state = cls.env.ref("l10n_br_base.res_partner_dell")

    def _make_po(self, partner, price=800.0, qty=1.0):
        return self.env["purchase.order"].create(
            {
                "partner_id": partner.id,
                "company_id": self.company.id,
                "fiscal_operation_id": self.fiscal_operation.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "product_qty": qty,
                            "price_unit": price,
                            "product_uom": self.product.uom_id.id,
                            "name": self.product.name,
                            "fiscal_operation_id": self.fiscal_operation.id,
                            "fiscal_operation_line_id": (
                                self.fiscal_operation_line.id
                            ),
                        },
                    )
                ],
            }
        )

    def test_supplier_comparison_same_price(self):
        """Mesmo preço de tabela, custos reais diferentes: fornecedor normal
        (ICMS credita) tem custo líquido MENOR que fornecedor Simples (nada
        credita, IPI soma). É o requisito central da decisão de compra."""
        po_normal = self._make_po(self.supplier_normal_sp)
        po_simples = self._make_po(self.supplier_simples_sp)

        line_normal = po_normal.order_line
        line_simples = po_simples.order_line

        self.assertGreater(line_normal.icms_value, 0)
        self.assertLess(
            line_normal.stock_cost_unit,
            line_simples.stock_cost_unit,
            "mesmo preço de tabela: comprar do fornecedor normal custa menos",
        )
        # Totais no cabeçalho para comparação rápida entre POs:
        self.assertAlmostEqual(
            po_normal.amount_stock_cost_total,
            line_normal.stock_cost_total,
            places=2,
        )
        self.assertAlmostEqual(
            line_normal.stock_cost_total,
            line_normal.stock_cost_unit * line_normal.product_qty,
            places=2,
        )

    def test_interstate_estimate_flag(self):
        """Compra interestadual: custo marcado como ESTIMATIVA (RF-C2) até o
        motor aplicar a alíquota interestadual na entrada (Fase B)."""
        po_same_state = self._make_po(self.supplier_normal_sp)
        po_other_state = self._make_po(self.supplier_other_state)

        self.assertFalse(po_same_state.order_line.stock_cost_estimated)
        self.assertFalse(po_same_state.stock_cost_estimated)
        self.assertTrue(po_other_state.order_line.stock_cost_estimated)
        self.assertTrue(po_other_state.stock_cost_estimated)

    def test_quantity_scales_total(self):
        """Total líquido escala com a quantidade."""
        po = self._make_po(self.supplier_normal_sp, qty=10.0)
        line = po.order_line
        self.assertAlmostEqual(
            po.amount_stock_cost_total, line.stock_cost_unit * 10.0, places=2
        )
