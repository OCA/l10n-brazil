# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from .common import StockEdiCase


class TestReceipt(StockEdiCase):
    def test_the_only_move_to_receive_is_the_receipt_of_the_origin(self):
        order = self._order()
        self._resolve_product()

        self.assertEqual(self.line.import_stock_move_id, self._moves(order))

    def test_a_received_move_not_invoiced_comes_first(self):
        order = self._order(quantity=10)
        self._receive(order, 4, backorder=True)
        done = self._moves(order).filtered(lambda move: move.state == "done")
        self.assertEqual(len(self._moves(order)), 2)

        self._resolve_product()

        self.assertEqual(self.line.import_stock_move_id, done)

    def test_a_received_and_invoiced_move_is_no_candidate(self):
        order = self._order(quantity=1)
        self._receive(order, 1)
        self._resolve_product()
        self.line.import_purchase_line_id = order.order_line
        self.document.action_generate_invoice()

        self.assertFalse(order.order_line._import_receipt_moves())

    def test_two_candidates_leave_the_receipt_to_the_person(self):
        order = self._order(quantity=10)
        self._receive(order, 4, backorder=True)
        self._receive(order, 3, backorder=True)

        self._resolve_product()

        self.assertEqual(self.line.import_purchase_line_id, order.order_line)
        self.assertFalse(self.line.import_stock_move_id)

    def test_a_return_is_never_the_receipt(self):
        order = self._order()
        warehouse = self.env["stock.warehouse"].search(
            [("company_id", "=", self.company.id)], limit=1
        )
        outgoing = self.env["stock.move"].create(
            {
                "name": "return",
                "product_id": self.product.id,
                "product_uom": self.unit.id,
                "product_uom_qty": 1,
                "location_id": warehouse.lot_stock_id.id,
                "location_dest_id": self.env.ref("stock.stock_location_suppliers").id,
                "picking_type_id": warehouse.out_type_id.id,
                "purchase_line_id": order.order_line.id,
            }
        )
        self.assertNotIn(outgoing, order.order_line._import_receipt_moves())
        self._resolve_product()
        self.assertEqual(self.line.import_stock_move_id, self._moves(order) - outgoing)
        self.assertFalse(self._rows(stock_move_id=outgoing.id))

    def test_choosing_the_move_sets_the_order_line(self):
        order = self._order()
        move = self._moves(order)
        self._resolve_product()
        self.line.write({"import_purchase_line_id": False})
        self.assertFalse(self.line.import_stock_move_id)

        self.line.import_stock_move_id = move

        self.assertEqual(self.line.import_purchase_line_id, order.order_line)
        self.assertEqual(self.line.import_origin_state, "resolved")

    def test_undoing_the_origin_takes_the_receipt_back(self):
        self._order()
        self._resolve_product()
        self.assertTrue(self.line.import_stock_move_id)

        self._rows(fiscal_document_id=self.document.id).action_no_order()

        self.assertFalse(self.line.import_stock_move_id)

    def test_a_document_issued_by_the_company_gets_no_receipt(self):
        self._order()
        document = self._imported_document(
            lines=[{"product_id": self.product.id}],
            issuer="company",
            partner_id=self.supplier.id,
        )

        document._edi_import_suggest()

        self.assertFalse(document.fiscal_line_ids.import_stock_move_id)
        self.assertFalse(self._rows(fiscal_document_id=document.id))
