# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from lxml import etree

from odoo.exceptions import UserError
from odoo.tests import tagged

from odoo.addons.l10n_br_fiscal_edi.tests.common import readable_field_names

from .common import PurchaseEdiCase


@tagged("post_install", "-at_install")
class TestSmartButtons(PurchaseEdiCase):
    """The document and the order point to each other, by the lines."""

    def _buyer(self):
        buyer = self._fiscal_user("button-buyer")
        buyer.groups_id |= self.env.ref("purchase.group_purchase_user")
        return buyer

    def _purchase_only(self):
        """A buyer with no fiscal group: sees the orders, not the documents."""
        user = self._fiscal_user("button-purchase-only")
        user.groups_id = [
            (3, self.env.ref("l10n_br_fiscal.group_user").id),
            (4, self.env.ref("purchase.group_purchase_user").id),
        ]
        return user

    def _arch(self, record, user):
        record = record.with_user(user).with_context(
            allowed_company_ids=user.company_ids.ids
        )
        return etree.fromstring(record.get_view(view_type="form")["arch"])

    def _fresh(self):
        self.env.flush_all()
        self.env.invalidate_all()

    def _linked(self):
        order = self._order()
        self._resolve_product()
        self.line.import_purchase_line_id = order.order_line
        return order

    def test_the_document_counts_and_opens_its_only_order(self):
        order = self._linked()
        self._fresh()

        document = self.document.with_user(self._buyer())

        self.assertEqual(document.import_purchase_order_count, 1)
        self.assertEqual(document.import_purchase_order_ids, order)
        action = document.action_view_import_purchase_orders()
        self.assertEqual(action["res_model"], "purchase.order")
        self.assertEqual(action["res_id"], order.id)
        self.assertEqual(action["views"], [(False, "form")])

    def test_the_document_opens_the_list_when_the_lines_point_to_several_orders(
        self,
    ):
        first = self._order()
        second = self._order()
        other = self.line.copy({"document_id": self.document.id})
        self._resolve_product()
        self._resolve_product(other)
        self.line.import_purchase_line_id = first.order_line
        other.import_purchase_line_id = second.order_line
        self._fresh()

        document = self.document.with_user(self._buyer())

        self.assertEqual(document.import_purchase_order_count, 2)
        action = document.action_view_import_purchase_orders()
        self.assertFalse(action.get("res_id"))
        self.assertEqual(sorted(action["domain"][0][2]), sorted((first | second).ids))

    def test_a_suggested_origin_counts_too(self):
        order = self._order()
        self._resolve_product()
        self.assertEqual(self.line.import_origin_state, "suggested")
        self._fresh()

        document = self.document.with_user(self._buyer())

        self.assertEqual(document.import_purchase_order_ids, order)

    def test_a_document_without_origin_has_no_orders(self):
        self._order()
        self._fresh()

        document = self.document.with_user(self._buyer())

        self.assertEqual(document.import_purchase_order_count, 0)

    def test_the_order_counts_and_opens_the_documents(self):
        order = self._linked()
        other = self._imported_document(lines=[{}])
        other.fiscal_line_ids.write({"product_id": self.product.id})
        other.fiscal_line_ids.import_purchase_line_id = order.order_line
        self._fresh()

        fiscal_buyer = self._buyer()
        found = order.with_user(fiscal_buyer)

        self.assertEqual(found.import_document_count, 2)
        action = found.action_view_import_documents()
        self.assertEqual(action["res_model"], "l10n_br_fiscal.document")
        self.assertEqual(
            sorted(action["domain"][0][2]), sorted((self.document | other).ids)
        )

        other.fiscal_line_ids.import_purchase_line_id = False
        self._fresh()
        found = order.with_user(fiscal_buyer)
        self.assertEqual(found.import_document_count, 1)
        action = found.action_view_import_documents()
        self.assertEqual(action["res_id"], self.document.id)

    def test_the_count_of_a_list_of_orders_is_read_once(self):
        first = self._linked()
        second = self._order()
        self._fresh()

        orders = (first | second).with_user(self._buyer())

        self.assertEqual(orders.mapped("import_document_count"), [1, 0])

    def test_the_buttons_follow_the_groups(self):
        order = self._linked()
        self._fresh()
        fiscal = self._fiscal_user("button-fiscal")
        buyer = self._buyer()
        purchase_only = self._purchase_only()

        # the pure fiscal user reads the whole form and sees no purchase button
        arch = self._arch(self.document, fiscal)
        self.assertFalse(
            arch.xpath("//button[@name='action_view_import_purchase_orders']")
        )
        self.assertFalse(arch.xpath("//field[@name='import_purchase_order_count']"))
        self._read_form(self._as(self.document, fiscal), arch)
        # the buyer who has the fiscal group sees it
        arch = self._arch(self.document, buyer)
        self.assertTrue(
            arch.xpath("//button[@name='action_view_import_purchase_orders']")
        )
        self._read_form(self._as(self.document, buyer), arch)
        # the order form: the document button is for the fiscal group
        arch = self._arch(order, buyer)
        self.assertTrue(arch.xpath("//button[@name='action_view_import_documents']"))
        self._read_form(self._as(order, buyer), arch)
        arch = self._arch(order, purchase_only)
        self.assertFalse(arch.xpath("//button[@name='action_view_import_documents']"))
        self.assertFalse(arch.xpath("//field[@name='import_document_count']"))
        self._read_form(self._as(order, purchase_only), arch)

    def test_the_line_opens_the_suggested_and_the_resolved_origin(self):
        order = self._order()
        self._resolve_product()
        self.assertEqual(self.line.import_origin_state, "suggested")

        action = self.line.action_open_import_origin()

        self.assertEqual(action["views"], [(False, "form")])
        self.assertEqual(action["type"], "ir.actions.act_window")
        # the link modules open their own record (a receipt) first
        if action["res_model"] == "purchase.order":
            self.assertEqual(action["res_id"], order.id)
        self.line.import_purchase_line_id = order.order_line
        self.assertEqual(self.line.import_origin_state, "resolved")
        again = self.line.action_open_import_origin()
        self.assertIn(again["res_model"], ("purchase.order", "stock.picking"))

    def test_a_line_without_origin_has_nothing_to_open(self):
        self._resolve_product()

        with self.assertRaisesRegex(UserError, "no origin"):
            self.line.action_open_import_origin()

    def test_the_button_of_the_line_is_for_the_purchase_users(self):
        self._linked()
        self._fresh()
        document = self.document
        name = "//button[@name='action_open_import_origin']"

        fiscal_arch = self._arch(document, self._fiscal_user("line-fiscal"))
        buyer_arch = self._arch(document, self._buyer())

        self.assertFalse(fiscal_arch.xpath(name))
        button = buyer_arch.xpath(name)
        self.assertTrue(button)
        self.assertIn("import_origin_state", button[0].get("modifiers"))

    def _as(self, record, user):
        return record.with_user(user).with_context(
            allowed_company_ids=user.company_ids.ids
        )

    def _read_form(self, record, arch):
        """The fields of the form, as the user reads them (the cache of the
        superuser does not stand in for the rights of the user)."""
        names = readable_field_names(
            record, [node.get("name") for node in arch.iter("field")]
        )
        record.read(names)
