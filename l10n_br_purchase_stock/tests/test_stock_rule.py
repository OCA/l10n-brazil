# Copyright (C) 2023-Today - Akretion (<http://www.akretion.com>).
# @author Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase


class StockRuleTest(TransactionCase):
    """Test Stock Rule"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def test_stock_rule_purchase(self):
        """
        Test Stock Rule related to Purchase
        """
        warehouse_1 = self.env["stock.warehouse"].search(
            [("company_id", "=", self.env.user.id)], limit=1
        )
        warehouse_1 = warehouse_1.write({"reception_steps": "two_steps"})
        self.env.ref("purchase_stock.route_warehouse0_buy")
        orderpoint = self.env["stock.warehouse.orderpoint"].create(
            {
                "product_id": self.env.ref("product.product_product_12").id,
                "product_min_qty": 1000.0,
            }
        )

        # Run scheduler
        self.env["procurement.group"].run_scheduler()

        orderpoint.action_replenish()
        orderpoint.action_replenish_auto()
        po_line = self.env["purchase.order.line"].search(
            [("orderpoint_id", "=", orderpoint.id)]
        )
        self.assertTrue(po_line.fiscal_operation_id, "Missing Fiscal Operation.")
        po_line._onchange_fiscal_operation_id()
        po_line._onchange_fiscal_operation_line_id()
        self.assertTrue(
            po_line.fiscal_operation_line_id,
            "Missing Fiscal Operation Line in Purchase Order.",
        )
        po_order = po_line.order_id
        self.assertTrue(
            po_order.fiscal_operation_id, "Missing Fiscal Operation in Purchase Order."
        )
        po_order.button_confirm()
        picking = po_order.picking_ids
        self.assertTrue(
            picking.fiscal_operation_id, "Missing Fiscal Operation in Picking."
        )
        for line in picking.move_lines:
            self.assertEqual(line.invoice_state, "2binvoiced")
            # Valida presença dos campos principais para o mapeamento Fiscal
            line._onchange_fiscal_operation_id()
            line._onchange_fiscal_operation_line_id()
            self.assertTrue(
                line.fiscal_operation_id, "Missing Fiscal Operation in Stock Move."
            )

            self.assertTrue(
                line.fiscal_operation_line_id,
                "Missing Fiscal Operation Line in Stock Move.",
            )

        picking.action_confirm()
        # Necessario para testar
        # l10n_br_purchase_stock/models/stock_rule.py  Linhas 18-23
        product_mto = self.env.ref("product.product_product_16")
        product_mto.route_ids |= self.env.ref("stock.route_warehouse0_mto")
        orderpoint_2 = self.env["stock.warehouse.orderpoint"].create(
            {
                "product_id": product_mto.id,
                "product_min_qty": 150.0,
                "route_id": self.env.ref("stock.route_warehouse0_mto").id,
            }
        )

        # Run scheduler
        self.env["procurement.group"].run_scheduler()
        orderpoint_2.action_replenish()
        orderpoint_2.action_replenish_auto()
