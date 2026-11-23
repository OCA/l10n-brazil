# Copyright (C) 2023-Today - Akretion (<http://www.akretion.com>).
# @author Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import Command
from odoo.tests.common import TransactionCase

from odoo.addons.l10n_br_fiscal.tests.tools import load_fiscal_fixture_files


class StockRuleTest(TransactionCase):
    """Test Stock Rule"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # The demo products are not installed by the OCA CI of 19.0
        if not cls.env.ref("product.product_product_12", raise_if_not_found=False):
            load_fiscal_fixture_files(cls.env)

    def test_stock_rule_purchase(self):
        """
        Test Stock Rule related to Purchase
        """
        warehouse_1 = self.env["stock.warehouse"].search(
            [("company_id", "=", self.env.user.id)], limit=1
        )
        warehouse_1 = warehouse_1.write({"reception_steps": "two_steps"})
        self.env.ref("purchase_stock.route_warehouse0_buy")
        # Set by the demo data: the pickings of the purchase orders are invoiced
        self.env.company.purchase_invoicing_policy = "stock_picking"
        product = self.env.ref("product.product_product_12")
        # Without demo data the product fixtures have no vendor nor buy route
        vendor = self.env["res.partner"].create({"name": "Vendor"})
        buy_route = self.env.ref("purchase_stock.route_warehouse0_buy")
        for demo_product in product | self.env.ref("product.product_product_16"):
            if not demo_product.seller_ids:
                demo_product.write(
                    {
                        "is_storable": True,
                        "route_ids": [Command.link(buy_route.id)],
                        "seller_ids": [Command.create({"partner_id": vendor.id})],
                    }
                )
        orderpoint = self.env["stock.warehouse.orderpoint"].create(
            {
                "product_id": product.id,
                "product_min_qty": 1000.0,
                "product_max_qty": 1000.0,
            }
        )

        # Run scheduler
        self.env["stock.rule"].run_scheduler()

        orderpoint.action_replenish()
        orderpoint.action_replenish_auto()
        po_line = self.env["purchase.order.line"].search(
            [("orderpoint_id", "=", orderpoint.id)]
        )
        self.assertTrue(po_line.fiscal_operation_id, "Missing Fiscal Operation.")
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
        for line in picking.move_ids:
            self.assertEqual(line.invoice_state, "2binvoiced")
            # Valida presença dos campos principais para o mapeamento Fiscal
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
                "product_max_qty": 150.0,
                "route_id": self.env.ref("stock.route_warehouse0_mto").id,
            }
        )

        # Run scheduler
        self.env["stock.rule"].run_scheduler()
        orderpoint_2.action_replenish()
        orderpoint_2.action_replenish_auto()
