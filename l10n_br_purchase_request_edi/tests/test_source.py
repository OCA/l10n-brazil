# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.exceptions import UserError

from .common import RequestEdiCase


class TestSource(RequestEdiCase):
    def test_an_approved_request_with_balance_is_a_source(self):
        request = self._request(quantity=10)
        line = request.line_ids

        row = self._rows(purchase_request_line_id=line.id)

        self.assertEqual(row.kind, "request")
        self.assertEqual(row.id, 4 * line.id + 3)
        self.assertEqual(row.reference, request.name)
        self.assertEqual((row.quantity, row.open_quantity), (10, 10))
        self.assertEqual(row.requested_by_id, self.env.user)
        self.assertEqual(row.line_state, "request_approved")
        self.assertFalse(row.partner_id)
        domain = self.document.action_open_origin_match()["domain"]
        self.assertIn(row, self.Match.search(domain))
        # once the supplier of the document is learned as a seller of the
        # product, the request is of that supplier
        self._resolve_product()
        self.assertEqual(
            self._rows(purchase_request_line_id=line.id).partner_id, self.supplier
        )

    def test_a_request_that_is_not_approved_is_not_a_source(self):
        draft = self._request(approve=False)
        rejected = self._request()
        rejected.button_rejected()

        self.assertFalse(
            self._rows(purchase_request_line_id=draft.line_ids.id)
            | self._rows(purchase_request_line_id=rejected.line_ids.id)
        )

    def test_the_balance_is_what_has_no_order_yet(self):
        request = self._request(quantity=10)
        line = request.line_ids
        order = self._order(quantity=4, confirm=False)
        line.purchase_lines = order.order_line

        self.assertEqual(self._rows(purchase_request_line_id=line.id).open_quantity, 6)

        order.order_line.product_qty = 10
        self.assertFalse(self._rows(purchase_request_line_id=line.id))

        order.order_line.product_qty = 4
        order.button_cancel()
        self.assertEqual(self._rows(purchase_request_line_id=line.id).open_quantity, 10)

    def test_the_preferred_supplier_of_another_partner_is_left_out(self):
        other = self.env["product.product"].create(
            {"name": "Other supplier product", "detailed_type": "consu"}
        )
        self.env["product.supplierinfo"].create(
            {
                "partner_id": self.company.partner_id.id,
                "product_tmpl_id": other.product_tmpl_id.id,
            }
        )
        own = self._request()
        theirs = self._request(product=other)
        self._resolve_product()
        self.line.product_id = False
        domain = self.document.action_open_origin_match()["domain"]
        self.env.flush_all()

        found = self.Match.search(domain)

        self.assertIn(own.line_ids, found.purchase_request_line_id)
        self.assertNotIn(theirs.line_ids, found.purchase_request_line_id)

    def test_a_request_cannot_be_matched_or_made_an_order_of_the_other_way(self):
        request = self._request()
        order = self._order()
        rows = self._note_rows_and_request(request)

        with self.assertRaisesRegex(UserError, "Create Order from Request"):
            (rows | self._rows(purchase_line_id=order.order_line.id)).action_match()
        with self.assertRaisesRegex(UserError, "Create Order from Request"):
            rows.action_create_order()

    def _as(self, user):
        return self.Match.with_user(user).with_context(
            allowed_company_ids=user.company_ids.ids,
            match_document_id=self.document.id,
        )

    def test_a_user_without_the_request_group_has_no_error_and_no_request(self):
        self._request()
        self._order()
        self._resolve_product()
        domain = self.document.action_open_origin_match()["domain"]
        buyer = self._fiscal_user("buyer-no-request")
        buyer.groups_id |= self.env.ref("purchase.group_purchase_user")
        fiscal = self._fiscal_user("fiscal-no-request-rows")

        for user in (buyer, fiscal):
            rows = self._as(user).search(domain)
            rows.read(list(rows.fields_get()))
            self.assertEqual(set(rows.mapped("kind")), {"note", "order"})
            self.assertFalse(self._as(user).search(domain + [("kind", "=", "request")]))
            with self.assertRaisesRegex(UserError, "no access to the purchase"):
                rows.action_create_order_from_request()

    def test_a_user_with_the_request_group_sees_the_requests(self):
        self._request()
        domain = self.document.action_open_origin_match()["domain"]
        user = self._fiscal_user("buyer-with-request")
        user.groups_id |= self.env.ref("purchase_request.group_purchase_request_user")

        rows = self._as(user).search(domain)

        self.assertIn("request", rows.mapped("kind"))
