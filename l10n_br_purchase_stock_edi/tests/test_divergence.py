# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from psycopg2 import IntegrityError

from odoo.tools import mute_logger

from .common import StockEdiCase


class TestDivergence(StockEdiCase):
    def _divergent_case(self):
        """Ordered 10 at 95, received 8; the document says 10 at 100."""
        order = self._order(quantity=10, price=95.0)
        self._receive(order, 8)
        self.line.write({"quantity": 10, "uom_id": self.unit.id, "price_unit": 100.0})
        self._resolve_product()
        self.line.import_purchase_line_id = order.order_line
        return order

    def test_the_document_line_against_the_order_and_the_receipt(self):
        self._divergent_case()
        line = self.line

        self.assertEqual(line.import_ordered_qty, 10)
        self.assertEqual(line.import_received_qty, 8)
        self.assertEqual(line.import_order_price_unit, 95.0)
        self.assertEqual(line.import_qty_difference, 2)
        self.assertAlmostEqual(line.import_price_difference, 5.0)
        self.assertTrue(line.import_divergent)
        self.assertTrue(self.document.import_divergent)
        found = self.env["l10n_br_fiscal.document"].search(
            [("import_divergent", "=", True)]
        )
        self.assertIn(self.document, found)
        rest = self.env["l10n_br_fiscal.document"].search(
            [("import_divergent", "=", False)]
        )
        self.assertNotIn(self.document, rest)

    def test_inside_the_tolerances_it_is_not_divergent(self):
        self._divergent_case()
        self.company.purchase_price_tolerance = 6.0
        self.company.purchase_quantity_tolerance = 30.0
        self.assertFalse(self.line.import_divergent)
        self.assertFalse(self.document.import_divergent)

        # the price alone out of its tolerance is enough
        self.company.purchase_price_tolerance = 5.0
        self.assertTrue(self.line.import_divergent)

    def test_the_tolerances_are_of_the_company_of_the_document(self):
        self._divergent_case()
        other = self.env["res.company"].create({"name": "Other company"})
        other.write(
            {"purchase_price_tolerance": 50.0, "purchase_quantity_tolerance": 50.0}
        )
        self.assertTrue(self.line.import_divergent)

        self.company.write(
            {"purchase_price_tolerance": 6.0, "purchase_quantity_tolerance": 30.0}
        )
        other.write(
            {"purchase_price_tolerance": 0.0, "purchase_quantity_tolerance": 0.0}
        )
        self.assertFalse(self.line.import_divergent)

    def test_a_line_that_matches_is_not_divergent(self):
        order = self._order(quantity=10, price=95.0)
        self._receive(order, 8)
        self.line.write({"quantity": 8, "uom_id": self.unit.id, "price_unit": 95.0})
        self._resolve_product()
        self.line.import_purchase_line_id = order.order_line

        self.assertEqual(self.line.import_qty_difference, 0)
        self.assertEqual(self.line.import_price_difference, 0)
        self.assertFalse(self.line.import_divergent)

    def test_a_line_without_order_has_nothing_to_compare(self):
        self._resolve_product()

        self.assertEqual(self.line.import_ordered_qty, 0)
        self.assertFalse(self.line.import_divergent)

    def test_a_note_not_received_yet_awaits_the_receipt_and_is_not_divergent(self):
        order = self._order(quantity=10, price=140.0)
        self.line.write({"quantity": 10, "uom_id": self.unit.id, "price_unit": 140.0})
        self._resolve_product()
        self.line.import_purchase_line_id = order.order_line

        self.assertTrue(self.line.import_awaiting_receipt)
        self.assertFalse(self.line.import_divergent)
        self.assertEqual(self.line.import_qty_difference, 0)
        self.assertTrue(self.document.import_awaiting_receipt)
        self.assertFalse(self.document.import_divergent)
        found = self.env["l10n_br_fiscal.document"].search(
            [("import_awaiting_receipt", "=", True)]
        )
        self.assertIn(self.document, found)
        # a document that points to no order line does not wait for a receipt
        other = self._imported_document(lines=[{}])
        self.assertNotIn(
            other,
            self.env["l10n_br_fiscal.document"].search(
                [("import_awaiting_receipt", "=", True)]
            ),
        )

    def test_a_note_received_and_matching_shows_nothing(self):
        order = self._order(quantity=10, price=140.0)
        self.line.write({"quantity": 10, "uom_id": self.unit.id, "price_unit": 140.0})
        self._resolve_product()
        self.line.import_purchase_line_id = order.order_line
        self._receive(order, 10)

        self.assertFalse(self.line.import_awaiting_receipt)
        self.assertFalse(self.line.import_divergent)
        self.assertFalse(self.document.import_awaiting_receipt)
        self.assertFalse(self.document.import_divergent)
        self.assertNotIn(
            self.document,
            self.env["l10n_br_fiscal.document"].search(
                [("import_awaiting_receipt", "=", True)]
            ),
        )

    def test_a_note_received_for_less_is_divergent(self):
        order = self._order(quantity=10, price=140.0)
        self.line.write({"quantity": 10, "uom_id": self.unit.id, "price_unit": 140.0})
        self._resolve_product()
        self.line.import_purchase_line_id = order.order_line
        self._receive(order, 6, backorder=True)

        self.assertFalse(self.line.import_awaiting_receipt)
        self.assertTrue(self.line.import_divergent)
        self.assertEqual(self.line.import_qty_difference, 4)

    def test_a_price_out_of_the_tolerance_is_divergent_even_before_the_receipt(self):
        order = self._order(quantity=10, price=140.0)
        self.line.write({"quantity": 10, "uom_id": self.unit.id, "price_unit": 150.0})
        self._resolve_product()
        self.line.import_purchase_line_id = order.order_line

        self.assertTrue(self.line.import_awaiting_receipt)
        self.assertTrue(self.line.import_divergent)
        self.company.purchase_price_tolerance = 10.0
        self.assertFalse(self.line.import_divergent)

    def test_a_note_for_more_than_the_order_is_divergent_before_the_receipt(self):
        order = self._order(quantity=10, price=140.0)
        self.line.write({"quantity": 12, "uom_id": self.unit.id, "price_unit": 140.0})
        self._resolve_product()
        self.line.import_purchase_line_id = order.order_line

        self.assertTrue(self.line.import_divergent)
        self.company.purchase_quantity_tolerance = 20.0
        self.assertFalse(self.line.import_divergent)

    def test_a_partial_receipt_still_compares_with_what_was_received(self):
        order = self._order(quantity=10, price=140.0)
        self.line.write({"quantity": 4, "uom_id": self.unit.id, "price_unit": 140.0})
        self._resolve_product()
        self.line.import_purchase_line_id = order.order_line
        self._receive(order, 4, backorder=True)

        self.assertFalse(self.line.import_divergent)
        self.assertFalse(self.line.import_awaiting_receipt)

    def test_the_bill_that_is_issued_before_the_receipt_awaits_it(self):
        order = self._order(quantity=10, price=100.0)
        self.line.write({"quantity": 10, "uom_id": self.unit.id, "price_unit": 100.0})
        self._resolve_product()
        self.line.import_purchase_line_id = order.order_line
        self.assertTrue(self.line.import_awaiting_receipt)

        action = self.document.action_generate_invoice()
        bill = self.env["account.move"].browse(action["res_id"])
        self.assertTrue(bill.purchase_awaiting_receipt)
        self.assertFalse(bill.purchase_divergent)
        self.assertEqual(bill.invoice_line_ids.purchase_received_qty, 0)

        self._receive(order, 10)
        bill.invoice_line_ids.invalidate_recordset()
        self.assertFalse(bill.purchase_awaiting_receipt)
        self.assertFalse(bill.purchase_divergent)

    def test_the_tolerances_cannot_be_negative(self):
        with self.assertRaises(IntegrityError), mute_logger(
            "odoo.sql_db"
        ), self.env.cr.savepoint():
            self.company.purchase_price_tolerance = -1.0
            self.company.flush_recordset()
