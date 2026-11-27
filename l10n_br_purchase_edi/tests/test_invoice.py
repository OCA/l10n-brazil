# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from .common import PurchaseEdiCase


class TestInvoice(PurchaseEdiCase):
    def _generate(self):
        action = self.document.action_generate_invoice()
        return self.env["account.move"].browse(action["res_id"])

    def _two_lines(self, quantity=3.0):
        second = self.line.copy({"document_id": self.document.id})
        for line in self.line | second:
            line.quantity = quantity
        for line in self.line | second:
            self._resolve_product(line)
        return second

    def test_bill_line_points_to_the_order_line(self):
        order = self._order(quantity=10)
        self._resolve_product()
        self.line.import_purchase_line_id = order.order_line

        move = self._generate()

        self.assertEqual(move.invoice_line_ids.purchase_line_id, order.order_line)
        self.assertIn(order.name, move.invoice_origin)
        self.assertEqual(order.order_line.qty_invoiced, 1)

    def test_lines_without_origin_stay_unlinked(self):
        self._resolve_product()

        move = self._generate()

        self.assertFalse(move.invoice_line_ids.purchase_line_id)

    def test_two_lines_share_an_order_line_while_they_fit(self):
        order = self._order(quantity=6)
        second = self._two_lines(quantity=3)
        (self.line | second).write({"import_purchase_line_id": order.order_line.id})

        move = self._generate()

        self.assertEqual(
            move.invoice_line_ids.mapped("purchase_line_id"), order.order_line
        )
        self.assertEqual(order.order_line.qty_invoiced, 6)

    def test_a_line_that_passes_the_balance_stays_unlinked(self):
        order = self._order(quantity=5)
        second = self._two_lines(quantity=3)
        (self.line | second).write({"import_purchase_line_id": order.order_line.id})

        move = self._generate()

        linked = move.invoice_line_ids.filtered("purchase_line_id")
        self.assertEqual(len(linked), 1)
        self.assertEqual(order.order_line.qty_invoiced, 3)
        self.assertIn("does not fit", move.message_ids[0].body)

    def test_bills_not_cancelled_take_from_the_balance(self):
        order = self._order(quantity=4)
        self._resolve_product()
        self.line.write({"quantity": 3, "import_purchase_line_id": order.order_line.id})
        move = self._generate()
        self.assertEqual(order.order_line._quantity_billed_elsewhere(), 3)

        move.button_cancel()

        self.assertEqual(order.order_line._quantity_billed_elsewhere(), 0)

    def test_the_bill_is_counted_once_in_the_balance(self):
        order = self._order(quantity=10)
        self._resolve_product()
        self.line.write({"quantity": 4, "import_purchase_line_id": order.order_line.id})
        self._generate()

        row = self._rows(purchase_line_id=order.order_line.id)

        self.assertEqual(order.order_line.qty_invoiced, 4)
        self.assertEqual(row.open_quantity, 6)
