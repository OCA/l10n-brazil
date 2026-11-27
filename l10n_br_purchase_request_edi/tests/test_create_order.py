# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.exceptions import UserError

from .common import RequestEdiCase


class TestCreateOrder(RequestEdiCase):
    def _buyer(self):
        groups = [
            "purchase.group_purchase_user",
            "purchase_request.group_purchase_request_user",
            "purchase_request.group_purchase_request_manager",
            "stock.group_stock_user",
            "l10n_br_fiscal.group_user",
        ]
        return self.env["res.users"].create(
            {
                "name": "Buyer",
                "login": "request-buyer",
                "company_ids": [(6, 0, self.env["res.company"].search([]).ids)],
                "company_id": self.company.id,
                "groups_id": [(6, 0, [self.env.ref(xmlid).id for xmlid in groups])],
            }
        )

    def _note(self, quantity=4.0, price=125.0):
        self.line.write(
            {"quantity": quantity, "price_unit": price, "uom_id": self.unit.id}
        )
        self._resolve_product()

    def test_the_order_takes_the_supplier_quantity_and_price_of_the_document(self):
        request = self._request(quantity=10, estimated=1000)
        self._note(quantity=4, price=125.0)
        rows = self._note_rows_and_request(request)

        action = rows.action_create_order_from_request()

        order = self.env["purchase.order"].browse(action["res_id"])
        self.assertEqual(order.partner_id, self.supplier)
        self.assertEqual(order.state, "purchase")
        self.assertEqual(order.order_line.product_qty, 4)
        self.assertEqual(order.order_line.price_unit, 125.0)
        self.assertIn(self.document.display_name, order.origin)
        # the trace: request, order, document
        self.assertEqual(request.line_ids.purchase_lines, order.order_line)
        self.assertEqual(self.line.import_request_line_id, request.line_ids)
        self.assertEqual(self.line.import_purchase_line_id, order.order_line)
        self.assertEqual(self.line.import_origin_state, "resolved")
        self.assertEqual(request.state, "in_progress")

    def test_an_order_waiting_for_approval_leaves_the_origin_suggested(self):
        self.company.write(
            {"po_double_validation": "two_step", "po_double_validation_amount": 1.0}
        )
        request = self._request()
        self._note()
        rows = self._note_rows_and_request(request)

        action = rows.with_user(self._buyer()).action_create_order_from_request()

        order = self.env["purchase.order"].browse(action["res_id"])
        self.assertEqual(order.state, "to approve")
        self.assertEqual(self.line.import_purchase_line_id, order.order_line)
        self.assertEqual(self.line.import_origin_state, "suggested")
        # the invoice follows the rules that already exist
        with self.assertRaisesRegex(UserError, "not decided"):
            self.document.action_generate_invoice()
        # a recomputation of the suggestion does not take the line away
        self.line._suggest_import_origin()
        self.assertEqual(self.line.import_purchase_line_id, order.order_line)

        order.button_approve(force=True)

        self.assertEqual(self.line.import_origin_state, "resolved")
        self.assertTrue(self.document.action_generate_invoice())

    def test_the_origin_chosen_by_a_person_later_leaves_the_request(self):
        request = self._request()
        self._note()
        rows = self._note_rows_and_request(request)
        rows.action_create_order_from_request()
        self.assertTrue(self.line.import_request_line_id)

        self._rows(fiscal_document_id=self.document.id).action_undo()

        self.assertFalse(self.line.import_request_line_id)
        self.assertEqual(self.line.import_origin_state, "pending")

    def test_a_line_without_product_takes_the_one_of_the_request(self):
        request = self._request()
        rows = self._note_rows_and_request(request)

        rows.action_create_order_from_request()

        self.assertEqual(self.line.product_id, self.product)
        self.assertEqual(self.line.import_origin_state, "resolved")

    def test_what_does_not_fit_is_refused(self):
        request = self._request()
        self._note()
        rows = self._note_rows_and_request(request)
        self.line.product_id = self.env["product.product"].create({"name": "Other"})
        with self.assertRaisesRegex(UserError, "not the product"):
            rows.action_create_order_from_request()
        self._resolve_product()

        request.line_ids.cancelled = True
        with self.assertRaisesRegex(UserError, "is not approved"):
            rows.action_create_order_from_request()

    def test_a_unit_nobody_confirmed_is_not_converted_silently(self):
        request = self._request()
        self._note()
        self.line.write(
            {"partner_uom_code": "XYZ", "uom_id": False, "import_uom_id": False}
        )

        with self.assertRaisesRegex(UserError, "was not confirmed"):
            self._note_rows_and_request(request).action_create_order_from_request()

    def test_creating_the_order_does_not_write_on_the_partner(self):
        request = self._request()
        self._note()
        before = (self.supplier.name, self.supplier.write_date)

        action = self._note_rows_and_request(request).action_create_order_from_request()

        order = self.env["purchase.order"].browse(action["res_id"])
        self.assertEqual(order.partner_id, self.supplier)
        self.assertEqual((self.supplier.name, self.supplier.write_date), before)

    def test_a_document_issued_by_the_company_gets_no_request_origin(self):
        self._request()
        document = self._imported_document(
            lines=[{"product_id": self.product.id}],
            issuer="company",
            partner_id=self.supplier.id,
        )

        document._edi_import_suggest()

        line = document.fiscal_line_ids
        self.assertFalse(line.import_request_line_id)
        self.assertFalse(self._rows(fiscal_document_id=document.id))

    def test_a_fiscal_user_without_the_request_group_changes_the_origin(self):
        request = self._request()
        self._note()
        self._note_rows_and_request(request).action_create_order_from_request()
        user = self._fiscal_user("fiscal-no-request")
        line = self.line.with_user(user).with_context(
            allowed_company_ids=user.company_ids.ids
        )

        line.import_purchase_line_id = False
        line._suggest_import_origin()

        self.assertFalse(self.line.sudo().import_request_line_id)
