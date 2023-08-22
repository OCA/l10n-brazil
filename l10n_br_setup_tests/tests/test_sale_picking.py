# Copyright (C) 2023 - Engenere (<https://engenere.one>).
# @author Antônio S. Pereira Neto <neto@engenere.one>


from odoo.tests.common import TransactionCase


class SalePickingTest(TransactionCase):
    """Tests the creation of picking from the sales order."""

    def setUp(self):
        super().setUp()

        # Create a product Kit and components.
        self.product_kit = self.env["product.product"].create(
            {"name": "Kit", "type": "product"}
        )
        self.product_kit_component1 = self.env["product.product"].create(
            {"name": "Kit Component 1", "type": "product"}
        )
        self.product_kit_component2 = self.env["product.product"].create(
            {"name": "Kit Component 2", "type": "product"}
        )
        # Create a BOM for the product Kit.
        self.bom = self.env["mrp.bom"].create(
            {
                "product_id": self.product_kit.id,
                "product_tmpl_id": self.product_kit.product_tmpl_id.id,
                "product_qty": 1,
                "type": "phantom",  # Kit
                "bom_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product_kit_component1.id,
                            "product_qty": 1,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "product_id": self.product_kit_component2.id,
                            "product_qty": 1,
                        },
                    ),
                ],
            }
        )
        self.partner = self.env["res.partner"].create({"name": "Test client"})
        self.so = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "client_order_ref": "SO1",
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product_kit.id,
                            "product_uom_qty": 1,
                            "price_unit": 1,
                        },
                    ),
                ],
            }
        )

    def test_kit_sale_picking(self):
        """Test that the picking is created with the components of the kit."""
        self.so.action_confirm()

        move_lines = self.so.picking_ids.move_lines
        self.assertEqual(len(move_lines), 2)

        move1 = move_lines.sorted()[0]
        self.assertEqual(move1.product_id, self.product_kit_component1)
        self.assertEqual(move1.product_qty, 1)

        move2 = move_lines.sorted()[1]
        self.assertEqual(move2.product_id, self.product_kit_component2)
        self.assertEqual(move2.product_qty, 1)
