# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import TransactionCase, tagged

KEY_REQUEST = "35261011765432000100550010000040011400100017"


@tagged("post_install", "-at_install")
class TestDemo(TransactionCase):
    """The reviewer finds an approved request and the note of its product with no
    order, and can create the order from the request right away."""

    def setUp(self):
        super().setUp()
        if not self.env.ref("l10n_br_purchase_request_edi.demo_request", False):
            self.skipTest("No demo data")
        self.request = self.env.ref("l10n_br_purchase_request_edi.demo_request")
        self.document = self.env["l10n_br_fiscal.document"].search(
            [("document_key", "=", KEY_REQUEST)]
        )

    def test_the_request_is_approved_and_the_note_has_no_order(self):
        self.assertEqual(self.request.state, "approved")
        self.assertEqual(self.document.state_edoc, "em_digitacao")
        line = self.document.fiscal_line_ids
        self.assertEqual(line.import_origin_state, "pending")
        self.assertFalse(line.import_purchase_line_id)

    def test_the_order_is_created_from_the_request(self):
        company = self.document.company_id
        match = self.env["l10n_br_purchase_edi.match"].with_company(company)
        self.env.flush_all()
        self.env.invalidate_all()
        rows = match.search(
            [("fiscal_document_id", "=", self.document.id)]
        ) | match.search([("purchase_request_line_id", "=", self.request.line_ids.id)])

        action = rows.action_create_order_from_request()

        order = self.env["purchase.order"].browse(action["res_id"])
        self.assertEqual(order.company_id, company)
        self.assertEqual(
            self.document.fiscal_line_ids.import_purchase_line_id, order.order_line
        )
        # the smart buttons of the document and of the request
        self.assertEqual(self.document.import_request_ids, self.request)
        self.assertEqual(self.request.import_document_ids, self.document)
        self.assertEqual(self.document.import_purchase_order_ids, order)
