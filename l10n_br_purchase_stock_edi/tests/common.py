# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.l10n_br_purchase_edi.tests.common import PurchaseEdiCase


class StockEdiCase(PurchaseEdiCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product = cls.env["product.product"].create(
            {"name": "Stocked product", "detailed_type": "product"}
        )

    def _receive(self, order, quantity, backorder=False):
        picking = order.picking_ids.filtered(lambda pick: pick.state != "done")[:1]
        picking.action_assign()
        picking.move_ids.quantity_done = quantity
        picking.with_context(
            cancel_backorder=not backorder, skip_backorder=backorder
        )._action_done()
        self.assertEqual(picking.state, "done")
        return picking

    def _moves(self, order):
        return order.order_line.move_ids
