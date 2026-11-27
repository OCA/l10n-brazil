# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import TransactionCase, tagged

KEY_INVOICED = "35261011765432000100550010000020011200100014"
KEY_QUOTATION = "35261011765432000100550010000020021200200024"
KEY_WITHOUT_ORDER = "35261011765432000100550010000020031200300034"


@tagged("post_install", "-at_install")
class TestDemo(TransactionCase):
    """The demo data walks the life cycle: what the reviewer finds after the
    install is what the screens and the videos use."""

    def setUp(self):
        super().setUp()
        if not self.env.ref("l10n_br_purchase_edi.demo_supplier", False):
            self.skipTest("No demo data")

    def _line(self, key):
        document = self.env["l10n_br_fiscal.document"].search(
            [("document_key", "=", key)]
        )
        self.assertEqual(len(document), 1)
        return document.fiscal_line_ids

    def test_the_declared_note_is_invoiced_and_the_order_shows_it(self):
        line = self._line(KEY_INVOICED)
        order = self.env.ref("l10n_br_purchase_edi.demo_order_confirmed")

        # the supplier has no mapping of the product: it came from the order
        self.assertEqual(line.product_id, order.order_line.product_id)
        # the note says what the order says
        self.assertEqual(line.price_unit, order.order_line.price_unit)
        self.assertEqual(line.quantity, order.order_line.product_qty)
        self.assertEqual(line.import_origin_state, "resolved")
        self.assertEqual(line.import_purchase_line_id, order.order_line)
        self.assertEqual(line.document_id.state_edoc, "autorizada")
        bill = line.document_id.move_ids
        self.assertEqual(bill.state, "posted")
        self.assertEqual(bill.company_id, line.document_id.company_id)
        self.assertEqual(order.invoice_status, "invoiced")
        # the smart buttons of the document and of the order
        self.assertEqual(line.document_id.import_purchase_order_ids, order)
        self.assertEqual(line.document_id.move_count, 1)
        self.assertEqual(order.import_document_ids, line.document_id)

    def test_the_note_of_the_quotation_waits_for_the_review(self):
        line = self._line(KEY_QUOTATION)
        quotation = self.env.ref("l10n_br_purchase_edi.demo_order_quotation")

        self.assertEqual(line.import_origin_state, "pending")
        self.assertFalse(line.document_id.move_ids)
        self.assertEqual(quotation.state, "draft")
        self.assertEqual(line.product_id, quotation.order_line.product_id)

    def test_the_note_without_order_is_decided(self):
        line = self._line(KEY_WITHOUT_ORDER)

        self.assertEqual(line.import_origin_state, "no_order")
        self.assertFalse(line.import_purchase_line_id)
