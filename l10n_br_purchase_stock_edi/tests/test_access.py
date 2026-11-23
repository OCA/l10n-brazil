# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.exceptions import AccessError
from odoo.tests import tagged

from .common import StockEdiCase


@tagged("post_install", "-at_install")
class TestReceiptAccess(StockEdiCase):
    """The decisions about the receipt are controlled writes of the real user."""

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

    def _no_order_rows(self):
        self._resolve_product()
        rows = self._rows(fiscal_document_id=self.document.id)
        rows.action_no_order()
        return self._rows(fiscal_document_id=self.document.id)

    def test_a_user_of_another_company_cannot_create_the_receipt(self):
        rows = self._no_order_rows()
        user = self._user(
            "stock-other-company",
            self.other_company,
            "l10n_br_fiscal.group_user",
            "stock.group_stock_user",
        )

        with self.assertRaises(AccessError):
            self._as(rows, user).action_create_receipt()

        self.assertFalse(self.line.import_stock_move_id)

    def test_a_user_of_another_company_cannot_open_the_receipt(self):
        order = self._order(quantity=10)
        self._resolve_product()
        self.line.import_purchase_line_id = order.order_line
        rows = self._rows(fiscal_document_id=self.document.id)
        user = self._user(
            "stock-other-company-open",
            self.other_company,
            "l10n_br_fiscal.group_user",
            "stock.group_stock_user",
        )

        with self.assertRaises(AccessError):
            self._as(rows, user).action_open_receipt()

    def test_a_manager_of_another_company_cannot_mark_no_stock_entry(self):
        rows = self._no_order_rows()
        user = self._user(
            "manager-other-company",
            self.other_company,
            "l10n_br_fiscal.group_user",
            "purchase.group_purchase_manager",
        )

        with self.assertRaises(AccessError):
            self._as(rows, user).action_no_stock_entry()

        self.assertFalse(self.line.import_no_stock_entry)

    def test_the_screen_writes_the_receipt_of_the_origin_only(self):
        rows = self._no_order_rows()

        self.assertIn("import_stock_move_id", rows._origin_fields())
        with self.assertRaises(AccessError):
            rows._write_origin(self.line, {"quantity": 99.0})

    def test_the_filter_of_the_bills_leaves_out_the_paid_ones(self):
        order = self._order(quantity=10, price=100.0)
        self.line.write({"quantity": 10, "uom_id": self.unit.id, "price_unit": 150.0})
        self._resolve_product()
        self.line.import_purchase_line_id = order.order_line
        action = self.document.action_generate_invoice()
        bill = self.env["account.move"].browse(action["res_id"])
        self.assertTrue(bill.purchase_divergent)
        self.assertIn(
            bill, self.env["account.move"].search([("purchase_divergent", "=", True)])
        )

        bill.invalidate_recordset(["payment_state"])
        self.env.cr.execute(
            "UPDATE account_move SET payment_state = 'paid' WHERE id = %s", [bill.id]
        )
        bill.invalidate_recordset(["payment_state"])

        self.assertNotIn(
            bill, self.env["account.move"].search([("purchase_divergent", "=", True)])
        )

    def test_a_buyer_with_stock_rights_creates_the_receipt_from_the_menu(self):
        rows = self._no_order_rows()
        buyer = self._user(
            "stock-buyer-menu",
            self.company,
            "purchase.group_purchase_user",
            "stock.group_stock_user",
        )

        action = self._as(rows, buyer).action_create_receipt()

        picking = self.env["stock.picking"].browse(action["res_id"])
        self.assertEqual(self.line.import_stock_move_id.picking_id, picking)

    def test_a_buyer_with_stock_rights_opens_the_receipt_from_the_menu(self):
        order = self._order(quantity=10)
        self._resolve_product()
        self.line.import_purchase_line_id = order.order_line
        rows = self._rows(fiscal_document_id=self.document.id)
        buyer = self._user(
            "stock-buyer-open",
            self.company,
            "purchase.group_purchase_user",
            "stock.group_stock_user",
        )

        action = self._as(rows, buyer).action_open_receipt()

        self.assertEqual(action["res_id"], order.picking_ids.id)
