# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from lxml import etree

from odoo.exceptions import AccessError, UserError
from odoo.osv import expression
from odoo.tests import tagged
from odoo.tools.safe_eval import safe_eval

from .common import PurchaseEdiCase


@tagged("post_install", "-at_install")
class TestMatchAccess(PurchaseEdiCase):
    """The decisions of the screen are controlled writes of the real user: only
    the fields of the origin, on the documents of his companies. The buyer
    decides the origin with no right on the fiscal lines; the product and the
    de-para stay with the fiscal profile."""

    def _user(self, login, groups, companies=None):
        companies = companies or self.company
        user = self._fiscal_user(login, companies)
        user.groups_id = [(5, 0, 0)] + [
            (4, self.env.ref(xmlid).id) for xmlid in ("base.group_user",) + groups
        ]
        return user

    def _as(self, rows, user):
        return rows.with_user(user).with_context(
            allowed_company_ids=user.company_ids.ids
        )

    def _note_rows(self):
        self._resolve_product()
        return self._rows(fiscal_document_id=self.document.id)

    def test_a_user_of_another_company_cannot_decide_the_origin(self):
        rows = self._note_rows()
        user = self._user(
            "other-company-buyer",
            ("l10n_br_fiscal.group_user", "purchase.group_purchase_user"),
            companies=self.other_company,
        )

        for action in ("action_no_order", "action_undo"):
            with self.assertRaises(AccessError):
                getattr(self._as(rows, user), action)()

        self.assertNotEqual(self.line.import_origin_state, "no_order")

    def test_a_user_of_the_company_decides_the_origin(self):
        rows = self._note_rows()
        user = self._user(
            "company-buyer",
            ("l10n_br_fiscal.group_user", "purchase.group_purchase_user"),
        )

        self._as(rows, user).action_no_order()

        self.assertEqual(self.line.import_origin_state, "no_order")

    def test_a_buyer_without_the_fiscal_group_decides_the_origin(self):
        order = self._order()
        rows = self._note_rows()
        rows |= self._rows(purchase_line_id=order.order_line.id, kind="order")
        user = self._user("buyer-only", ("purchase.group_purchase_user",))

        self._as(rows, user).action_match()

        self.assertEqual(self.line.import_purchase_line_id, order.order_line)
        self.assertEqual(self.line.import_origin_state, "resolved")
        # and takes it back
        self._as(self._rows(fiscal_document_id=self.document.id), user).action_undo()
        self.assertEqual(self.line.import_origin_state, "pending")

    def test_a_buyer_without_the_fiscal_group_cannot_change_the_product(self):
        order = self._order()
        self.line.product_id = False
        rows = self._rows(fiscal_document_id=self.document.id)
        rows |= self._rows(purchase_line_id=order.order_line.id, kind="order")
        user = self._user("buyer-only-product", ("purchase.group_purchase_user",))

        with self.assertRaises(AccessError):
            self._as(rows, user).action_match()

        self.assertFalse(self.line.product_id)
        self.assertFalse(self.line.import_purchase_line_id)

    def test_the_fiscal_profile_chooses_the_product_of_the_order(self):
        order = self._order()
        self.line.product_id = False
        rows = self._rows(fiscal_document_id=self.document.id)
        rows |= self._rows(purchase_line_id=order.order_line.id, kind="order")
        user = self._user(
            "fiscal-buyer-product",
            ("l10n_br_fiscal.group_user", "purchase.group_purchase_user"),
        )

        self._as(rows, user).action_match()

        self.assertEqual(self.line.product_id, self.product)

    def test_the_screen_writes_only_the_fields_of_the_origin(self):
        rows = self._note_rows()

        with self.assertRaises(AccessError):
            rows._write_origin(self.line, {"product_id": False})
        with self.assertRaises(AccessError):
            rows._write_origin(self.line, {"price_unit": 1.0})

    def test_the_fiscal_profile_reads_the_orders_of_its_company_only(self):
        order = self._order()
        self.env.flush_all()
        fiscal = self._user("fiscal-reader", ("l10n_br_fiscal.group_user",))
        other = self._user(
            "fiscal-reader-other",
            ("l10n_br_fiscal.group_user",),
            companies=self.other_company,
        )

        rows = self._as(self.Match, fiscal).search([("kind", "=", "order")])
        other_rows = self._as(self.Match, other).search([("kind", "=", "order")])

        self.assertIn(order, rows.purchase_order_id)
        self.assertNotIn(order, other_rows.purchase_order_id)

    def test_a_row_of_another_company_is_not_reached_by_id(self):
        order = self._order()
        rows = self._note_rows()
        rows |= self._rows(purchase_line_id=order.order_line.id, kind="order")
        user = self._user(
            "other-company-id",
            ("l10n_br_fiscal.group_user", "purchase.group_purchase_user"),
            companies=self.other_company,
        )

        with self.assertRaises(AccessError):
            self._as(rows, user).action_match()

        self.assertNotEqual(self.line.import_origin_state, "resolved")

    # the menu of the buyer ------------------------------------------------

    def _menu_action(self):
        return self.env.ref("l10n_br_purchase_edi.document_match_buyer_action").sudo()

    def _buyer(self, login="menu-buyer", companies=None):
        return self._user(login, ("purchase.group_purchase_user",), companies)

    def _open_menu(self, user):
        """The screen as the buyer opens it: the view and the rows."""
        action = self._menu_action()
        model = (
            self.env[action.res_model]
            .with_user(user)
            .with_context(allowed_company_ids=user.company_ids.ids)
        )
        arch = model.get_view(action.view_id.id or False, "tree")["arch"]
        domain = [
            "|",
            ("kind", "!=", "note"),
            ("line_state", "in", ("pending", "suggested")),
        ]
        names = [
            node.get("name")
            for node in etree.fromstring(arch).iter("field")
            if node.get("name") in model._fields
        ]
        return model.search_read(domain, names), arch

    def test_a_buyer_opens_the_menu_with_no_fiscal_right(self):
        self._order()
        self._resolve_product()
        self.env.flush_all()
        self.env.invalidate_all()
        buyer = self._buyer()

        rows, arch = self._open_menu(buyer)

        kinds = {row["kind"] for row in rows}
        self.assertTrue({"note", "order"} <= kinds)
        # the view of the buyer carries no fiscal model and no link to it
        self.assertNotIn("fiscal_document_id", arch)
        self.assertNotIn('name="action_open_document"', arch)

    def test_the_menu_is_for_the_purchase_users(self):
        menu = self.env.ref("l10n_br_purchase_edi.document_match_buyer_menu")
        fiscal = self._user("menu-fiscal", ("l10n_br_fiscal.group_user",))

        self.assertIn(self.env.ref("purchase.group_purchase_user"), menu.groups_id)
        visible = self.env["ir.ui.menu"].with_user(fiscal)._visible_menu_ids()
        self.assertNotIn(menu.id, visible)

    def test_the_buyer_decides_the_origin_from_the_menu(self):
        order = self._order()
        rows = self._note_rows()
        rows |= self._rows(purchase_line_id=order.order_line.id, kind="order")
        buyer = self._buyer("menu-buyer-decides")

        self._as(rows, buyer).action_match()

        self.assertEqual(self.line.import_origin_state, "resolved")

    def test_the_buyer_does_not_choose_the_product_from_the_menu(self):
        order = self._order()
        self.line.product_id = False
        rows = self._rows(fiscal_document_id=self.document.id)
        rows |= self._rows(purchase_line_id=order.order_line.id, kind="order")
        buyer = self._buyer("menu-buyer-product")

        with self.assertRaises(AccessError):
            self._as(rows, buyer).action_match()

        self.assertFalse(self.line.product_id)

    def test_the_link_to_the_document_is_for_the_fiscal_group(self):
        rows = self._note_rows()
        buyer = self._buyer("menu-buyer-link")
        fiscal = self._user("menu-fiscal-link", ("l10n_br_fiscal.group_user",))

        with self.assertRaisesRegex(UserError, "fiscal profile"):
            self._as(rows, buyer).action_open_document()
        action = self._as(rows, fiscal).action_open_document()

        self.assertEqual(action["res_id"], self.document.id)

    def test_a_buyer_of_another_company_does_not_see_the_lines(self):
        self._order()
        self._resolve_product()
        self.env.flush_all()
        self.env.invalidate_all()
        buyer = self._buyer("menu-buyer-other", companies=self.other_company)

        rows, _arch = self._open_menu(buyer)

        self.assertFalse(
            [row for row in rows if row["reference"] == self.document.document_number]
        )

    def _menu_rows(self, user, extra=None):
        """The rows of the screen of the menu for the buyer, with the domain of a
        filter of the search view."""
        model = self.Match.with_user(user).with_context(
            allowed_company_ids=user.company_ids.ids
        )
        self.env.flush_all()
        self.env.invalidate_all()
        return model.search_read(extra or [], ["kind", "line_state", "reference"])

    def _filter_domain(self, name):
        """The domain of a filter of the search view of the menu."""
        view = self.env.ref("l10n_br_purchase_edi.document_match_search")
        node = etree.fromstring(view.arch)
        filters = node.xpath("//filter[@name='%s']" % name)
        self.assertTrue(filters, name)
        return safe_eval(filters[0].get("domain"))

    def test_the_origin_filters_are_in_the_same_group_and_add_up(self):
        view = self.env.ref("l10n_br_purchase_edi.document_match_search")
        node = etree.fromstring(view.arch)
        names = [
            child.get("name") or child.tag
            for child in node.iter()
            if child.tag in ("filter", "separator")
            and child.getparent().tag == "search"
        ]
        first, second = names.index("pending_or_suggested"), names.index("resolved")

        # no separator between them: the filters of one group add up (OR)
        self.assertEqual(second, first + 1)
        self.assertNotIn("all_origins", names)

    def test_the_buyer_finds_the_resolved_note_and_undoes_it(self):
        order = self._order()
        rows = self._note_rows()
        rows |= self._rows(purchase_line_id=order.order_line.id, kind="order")
        buyer = self._buyer("menu-buyer-undo")
        reference = self.document.document_number
        both = expression.OR(
            [
                self._filter_domain("pending_or_suggested"),
                self._filter_domain("resolved"),
            ]
        )

        def seen(domain):
            return [
                row
                for row in self._menu_rows(buyer, domain)
                if row["kind"] == "note" and row["reference"] == reference
            ]

        pending = self._filter_domain("pending_or_suggested")
        resolved = self._filter_domain("resolved")
        self.assertTrue(seen(pending))
        self._as(rows, buyer).action_match()

        self.assertFalse(seen(pending))
        self.assertTrue(seen(resolved))
        # the default filter and the resolved one together show the decided note
        self.assertTrue(seen(both))
        undo = self._rows(fiscal_document_id=self.document.id, kind="note")
        self._as(undo, buyer).action_undo()
        self.assertEqual(self.line.import_origin_state, "pending")
        self.assertTrue(seen(both))
        self.assertTrue(seen(pending))
        self.assertFalse(seen(resolved))
