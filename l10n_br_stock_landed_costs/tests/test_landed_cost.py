# Copyright (C) 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.l10n_br_stock_account.tests.test_stock_valuation import (
    StockValuationNetCostCase,
)


class TestLandedCostNetCost(StockValuationNetCostCase):
    """Fase E — landed cost a partir de documento fiscal, pelo custo LÍQUIDO:
    o ICMS creditável do frete vira crédito fiscal e não é rateado no
    estoque; o valor líquido ajusta os SVLs dos recebimentos."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.freight_product = cls.env.ref("product.product_product_7")

    def _make_freight_document(self, price=100.0):
        """Documento fiscal de frete/despesa (mecânica de CT-e): linha com
        ICMS destacado creditável → custo líquido < valor do documento."""
        doc = self.env.ref("l10n_br_fiscal.demo_nfe_purchase_same_state").copy(
            {
                "partner_id": self.supplier_normal.id,
                "company_id": self.company.id,
            }
        )
        doc.fiscal_line_ids.unlink()
        line = self.env["l10n_br_fiscal.document.line"].create(
            {
                "document_id": doc.id,
                "name": "Frete rodoviário",
                "product_id": self.freight_product.id,
                "uom_id": self.freight_product.uom_id.id,
                "quantity": 1,
                "price_unit": price,
                "fiscal_operation_id": self.fiscal_operation.id,
                "fiscal_operation_line_id": self.fiscal_operation_line.id,
            }
        )
        return doc, line

    def test_landed_cost_from_fiscal_document(self):
        """Recebimento (SVL líquido) + documento de frete → landed cost pelo
        LÍQUIDO do frete → SVL ajustado = líquido da compra + líquido do
        frete."""
        self._set_cost_method("fifo")
        picking, move = self._make_incoming(self.supplier_normal)
        self._receive(picking)
        base_svl_value = sum(move.stock_valuation_layer_ids.mapped("value"))

        doc, line = self._make_freight_document(price=100.0)
        self.assertGreater(line.icms_value, 0, "frete com ICMS destacado")
        net_freight = line.stock_cost_unit * line.quantity
        self.assertLess(net_freight, 100.0, "líquido < valor do documento")

        doc.landed_cost_picking_ids = picking
        action = doc.action_create_landed_cost()
        landed = self.env["stock.landed.cost"].browse(action["res_id"])

        self.assertEqual(landed.fiscal_document_id, doc)
        self.assertEqual(len(landed.cost_lines), 1)
        self.assertAlmostEqual(landed.cost_lines.price_unit, net_freight, places=2)

        landed.compute_landed_cost()
        landed.button_validate()
        self.assertEqual(landed.state, "done")

        total_value = sum(
            self.env["stock.valuation.layer"]
            .search(
                [
                    ("product_id", "=", self.product.id),
                    ("company_id", "=", self.company.id),
                ]
            )
            .mapped("value")
        )
        self.assertAlmostEqual(
            total_value, base_svl_value + net_freight, places=2
        )

    def test_no_pickings_raises(self):
        """Sem recebimentos selecionados, a ação orienta o usuário."""
        doc, _line = self._make_freight_document()
        with self.assertRaises(Exception):
            doc.action_create_landed_cost()
