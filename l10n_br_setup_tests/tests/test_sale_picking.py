# Copyright (C) 2023 - Engenere (<https://engenere.one>).
# @author Antônio S. Pereira Neto <neto@engenere.one>


from odoo.tests.common import TransactionCase


class SalePickingTest(TransactionCase):
    """Tests the creation of picking from the sales order."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))

        # Create a product Kit and components.
        cls.product_kit = cls.env["product.product"].create(
            {"name": "Kit", "type": "product"}
        )
        cls.product_kit_component1 = cls.env["product.product"].create(
            {"name": "Kit Component 1", "type": "product"}
        )
        cls.product_kit_component2 = cls.env["product.product"].create(
            {"name": "Kit Component 2", "type": "product"}
        )
        # Create a BOM for the product Kit.
        cls.bom = cls.env["mrp.bom"].create(
            {
                "product_id": cls.product_kit.id,
                "product_tmpl_id": cls.product_kit.product_tmpl_id.id,
                "product_qty": 1,
                "type": "phantom",  # Kit
                "bom_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": cls.product_kit_component1.id,
                            "product_qty": 1,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "product_id": cls.product_kit_component2.id,
                            "product_qty": 1,
                        },
                    ),
                ],
            }
        )
        cls.partner = cls.env["res.partner"].create({"name": "Test client"})
        cls.so = cls.env["sale.order"].create(
            {
                "partner_id": cls.partner.id,
                "client_order_ref": "SO1",
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": cls.product_kit.id,
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
