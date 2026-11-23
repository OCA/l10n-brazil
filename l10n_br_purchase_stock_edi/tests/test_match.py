# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.exceptions import UserError

from .common import StockEdiCase


class TestMatch(StockEdiCase):
    def _split_order(self):
        """An order of 10 with 4 received (a done move) and 6 to come."""
        order = self._order(quantity=10)
        self._receive(order, 4, backorder=True)
        moves = self._moves(order)
        done = moves.filtered(lambda move: move.state == "done")
        return order, done, moves - done

    def test_the_tela_lists_receipts_pending_and_done_but_not_cancelled(self):
        order, done, pending = self._split_order()

        rows = self._rows(purchase_order_id=order.id, kind="receipt")

        self.assertEqual(rows.stock_move_id, done | pending)
        by_move = {row.stock_move_id: row for row in rows}
        self.assertEqual(by_move[done].line_state, "receipt_done")
        self.assertEqual(by_move[done].quantity, 4)
        self.assertEqual(by_move[pending].line_state, "receipt_pending")
        self.assertEqual(by_move[pending].id, 4 * pending.id + 2)
        pending._action_cancel()
        self.assertFalse(self._rows(stock_move_id=pending.id))

    def test_a_received_and_invoiced_move_leaves_the_tela(self):
        order = self._order(quantity=1)
        self._receive(order, 1)
        self.assertTrue(self._rows(kind="receipt", purchase_order_id=order.id))
        self._resolve_product()
        self.line.import_purchase_line_id = order.order_line
        self.document.action_generate_invoice()

        self.assertFalse(self._rows(kind="receipt", purchase_order_id=order.id))

    def test_match_takes_the_receipt_the_person_selected(self):
        order, done, pending = self._split_order()
        self._resolve_product()
        self.assertEqual(self.line.import_stock_move_id, done)
        rows = self._rows(fiscal_document_id=self.document.id)
        rows |= self._rows(purchase_line_id=order.order_line.id, kind="order")
        rows |= self._rows(stock_move_id=pending.id)

        rows.action_match()

        self.assertEqual(self.line.import_origin_state, "resolved")
        self.assertEqual(self.line.import_stock_move_id, pending)

    def test_match_refuses_a_receipt_of_another_order_line(self):
        order = self._order()
        other = self._order()
        rows = self._rows(fiscal_document_id=self.document.id)
        rows |= self._rows(purchase_line_id=order.order_line.id, kind="order")
        rows |= self._rows(stock_move_id=self._moves(other).id)

        with self.assertRaisesRegex(UserError, "does not belong"):
            rows.action_match()

    def test_open_receipt_proposes_the_quantity_and_validates_nothing(self):
        order = self._order(quantity=10)
        self._resolve_product()
        move = self._moves(order)
        self.assertEqual(move.quantity_done, 0)

        action = self._rows(fiscal_document_id=self.document.id).action_open_receipt()

        self.assertEqual(action["res_id"], order.picking_ids.id)
        self.assertEqual(move.quantity_done, self.line.quantity)
        self.assertNotEqual(order.picking_ids.state, "done")

    def test_open_receipt_does_not_overwrite_a_quantity_already_there(self):
        order = self._order(quantity=10)
        self._resolve_product()
        move = self._moves(order)
        move.quantity_done = 7

        self._rows(fiscal_document_id=self.document.id).action_open_receipt()

        self.assertEqual(move.quantity_done, 7)

    def test_open_receipt_needs_a_receipt(self):
        self._resolve_product()

        with self.assertRaisesRegex(UserError, "have a receipt"):
            self._rows(fiscal_document_id=self.document.id).action_open_receipt()
