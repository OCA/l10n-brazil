# Copyright (C) 2026  Raphaël Valyi - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields
from odoo.tests import TransactionCase


class TestStockMoveBillMatchingReferenceSQL(TransactionCase):
    """The stock.move side of the stock_picking_bill_matching duck-typing
    hook: explicit xPed/nItemPed reference when set, canonical
    (PO name, line position) derivation from purchase_line_id otherwise."""

    def _eval_ref(self, move_id):
        expr = self.env["stock.move"]._get_bill_matching_reference_sql("sm")
        self.env.cr.execute(
            f"SELECT ({expr}) FROM stock_move sm WHERE sm.id = %s", (move_id,)
        )
        return self.env.cr.fetchone()[0]

    def _create_confirmed_po(self, products):
        partner = self.env["res.partner"].create({"name": "Bill Match Vendor"})
        order = self.env["purchase.order"].create(
            {"partner_id": partner.id, "company_id": self.env.company.id}
        )
        for product in products:
            self.env["purchase.order.line"].create(
                {
                    "order_id": order.id,
                    "product_id": product.id,
                    "name": product.name,
                    "product_qty": 2.0,
                    "price_unit": 10.0,
                    "date_planned": fields.Datetime.now(),
                }
            )
        order.with_context(tracking_disable=True).button_confirm()
        return order

    def test_po_derived_reference(self):
        """No xPed filled anywhere: the move's reference is derived from its
        PO line as '<PO name>-<1-based position>', matching what the NFe
        import wizard synthesizes on the vendor bill side."""
        product = self.env["product.product"].create(
            {"name": "Match Ref Product A", "type": "product"}
        )
        other = self.env["product.product"].create(
            {"name": "Match Ref Product B", "type": "product"}
        )
        order = self._create_confirmed_po([product, other])
        moves = order.picking_ids.move_ids
        move_a = moves.filtered(lambda m: m.product_id == product)
        move_b = moves.filtered(lambda m: m.product_id == other)
        self.assertEqual(self._eval_ref(move_a.id), f"{order.name}-1")
        self.assertEqual(self._eval_ref(move_b.id), f"{order.name}-2")

    def test_explicit_reference_wins_and_normalizes(self):
        product = self.env["product.product"].create(
            {"name": "Match Ref Product C", "type": "product"}
        )
        order = self._create_confirmed_po([product])
        move = order.picking_ids.move_ids[0]
        move.partner_order = "XPED-9"
        move.partner_order_line = "003"
        self.assertEqual(self._eval_ref(move.id), "XPED-9-3")

    def test_no_reference_no_po_is_null(self):
        product = self.env["product.product"].create(
            {"name": "Match Ref Product D", "type": "product"}
        )
        location_src = self.env.ref("stock.stock_location_suppliers")
        dest = self.env.ref("stock.stock_location_stock")
        move = self.env["stock.move"].create(
            {
                "name": product.name,
                "product_id": product.id,
                "product_uom_qty": 1.0,
                "product_uom": product.uom_id.id,
                "location_id": location_src.id,
                "location_dest_id": dest.id,
            }
        )
        self.assertIsNone(self._eval_ref(move.id))
