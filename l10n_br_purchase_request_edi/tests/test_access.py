# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.exceptions import AccessError
from odoo.tests import tagged

from .common import RequestEdiCase


@tagged("post_install", "-at_install")
class TestRequestAccess(RequestEdiCase):
    """Creating the order from the request is a controlled write of the real
    user, on the documents of his companies."""

    def _user(self, login, companies, *groups):
        user = self._fiscal_user(login, companies)
        user.groups_id = [(5, 0, 0)] + [
            (4, self.env.ref(xmlid).id) for xmlid in ("base.group_user",) + groups
        ]
        return user

    def _as(self, rows, user):
        return rows.with_user(user).with_context(
            allowed_company_ids=user.company_ids.ids
        )

    def _rows_with_request(self):
        request = self._request()
        self.line.write({"quantity": 4, "price_unit": 125.0, "uom_id": self.unit.id})
        self._resolve_product()
        return self._note_rows_and_request(request)

    def test_a_user_of_another_company_cannot_create_the_order(self):
        rows = self._rows_with_request()
        user = self._user(
            "request-other-company",
            self.other_company,
            "l10n_br_fiscal.group_user",
            "purchase.group_purchase_manager",
            "purchase_request.group_purchase_request_manager",
        )

        with self.assertRaises(AccessError):
            self._as(rows, user).action_create_order_from_request()

        self.assertFalse(self.line.import_request_line_id)
        self.assertFalse(self.line.import_purchase_line_id)

    def test_a_buyer_without_the_fiscal_group_cannot_choose_the_product(self):
        request = self._request()
        self.line.write({"quantity": 4, "price_unit": 125.0, "uom_id": self.unit.id})
        self.line.product_id = False
        rows = self._note_rows_and_request(request)
        user = self._user(
            "request-buyer-no-fiscal",
            self.company,
            "purchase.group_purchase_manager",
            "purchase_request.group_purchase_request_manager",
        )

        with self.assertRaises(AccessError):
            self._as(rows, user).action_create_order_from_request()

        self.assertFalse(self.line.product_id)

    def test_the_screen_writes_the_request_of_the_origin(self):
        rows = self._rows_with_request()

        self.assertIn("import_request_line_id", rows._origin_fields())
        with self.assertRaises(AccessError):
            rows._write_origin(self.line, {"name": "x"})

    def test_the_buyer_sees_the_requests_of_the_menu_with_the_request_group(self):
        self._request()
        self._resolve_product()
        self.env.flush_all()
        self.env.invalidate_all()
        with_group = self._user(
            "menu-requester",
            self.company,
            "purchase.group_purchase_user",
            "purchase_request.group_purchase_request_user",
        )
        without_group = self._user(
            "menu-buyer-no-request", self.company, "purchase.group_purchase_user"
        )

        seen = self._as(self.Match, with_group).search([("kind", "=", "request")])
        hidden = self._as(self.Match, without_group).search([("kind", "=", "request")])

        self.assertTrue(seen)
        self.assertFalse(hidden)
