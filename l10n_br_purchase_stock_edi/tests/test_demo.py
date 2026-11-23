# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import TransactionCase, tagged

KEY_LOTS = "35261011765432000100550010000030011300100010"
KEY_WAITING = "35261011765432000100550010000030021300200020"


@tagged("post_install", "-at_install")
class TestDemo(TransactionCase):
    """The receipt of the demo order took the lots of the note and was validated."""

    def setUp(self):
        super().setUp()
        if not self.env.ref("l10n_br_purchase_stock_edi.demo_order_lot", False):
            self.skipTest("No demo data")

    def test_the_receipt_has_the_lots_of_the_note_and_is_done(self):
        order = self.env.ref("l10n_br_purchase_stock_edi.demo_order_lot")
        document = self.env["l10n_br_fiscal.document"].search(
            [("document_key", "=", KEY_LOTS)]
        )
        line = document.fiscal_line_ids

        self.assertEqual(line.import_origin_state, "resolved")
        self.assertEqual(line.import_purchase_line_id, order.order_line)
        picking = order.picking_ids
        self.assertEqual(picking.state, "done")
        lots = {
            move_line.lot_id.name: move_line.qty_done
            for move_line in picking.move_line_ids
        }
        self.assertEqual(lots, {"L-DEMO-01": 6.0, "L-DEMO-02": 4.0})
        self.assertEqual(order.order_line.qty_received, 10.0)
        # the note says what the order and the receipt say: nothing diverges
        self.assertFalse(line.import_divergent)
        self.assertEqual(line.import_price_difference, 0)
        self.assertEqual(line.import_qty_difference, 0)
        # the smart buttons of the document and of the receipt
        self.assertEqual(document.import_picking_ids, picking)
        self.assertEqual(picking.import_document_ids, document)
        self.assertEqual(document.import_purchase_order_ids, order)

    def test_the_note_of_the_order_not_received_awaits_the_receipt(self):
        order = self.env.ref("l10n_br_purchase_stock_edi.demo_order_waiting")
        document = self.env["l10n_br_fiscal.document"].search(
            [("document_key", "=", KEY_WAITING)]
        )
        line = document.fiscal_line_ids

        self.assertEqual(line.import_purchase_line_id, order.order_line)
        self.assertTrue(line.import_awaiting_receipt)
        self.assertFalse(line.import_divergent)
        self.assertTrue(document.import_awaiting_receipt)
        self.assertEqual(document.import_picking_ids, order.picking_ids)
        self.assertNotEqual(order.picking_ids.state, "done")

    def test_the_note_of_the_purchases_demo_is_received_too(self):
        order = self.env.ref("l10n_br_purchase_edi.demo_order_confirmed")
        document = self.env["l10n_br_fiscal.document"].search(
            [
                (
                    "document_key",
                    "=",
                    "35261011765432000100550010000020011200100014",
                )
            ]
        )

        self.assertEqual(order.picking_ids.state, "done")
        self.assertFalse(document.import_awaiting_receipt)
        self.assertFalse(document.import_divergent)
        self.assertEqual(order.order_line.qty_received, 5.0)
