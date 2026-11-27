# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from lxml import etree

from odoo.tests import tagged

from odoo.addons.l10n_br_fiscal_edi.tests.common import readable_field_names

from .common import StockEdiCase


@tagged("post_install", "-at_install")
class TestSmartButtons(StockEdiCase):
    """The document and the receipt point to each other, by the lines."""

    def _storekeeper(self):
        user = self._fiscal_user("button-storekeeper")
        user.groups_id |= self.env.ref("stock.group_stock_user")
        return user

    def _as(self, record, user):
        return record.with_user(user).with_context(
            allowed_company_ids=user.company_ids.ids
        )

    def _arch(self, record, user):
        return etree.fromstring(
            self._as(record, user).get_view(view_type="form")["arch"]
        )

    def _read_form(self, record, arch):
        names = readable_field_names(
            record, [node.get("name") for node in arch.iter("field")]
        )
        record.read(names)

    def _fresh(self):
        self.env.flush_all()
        self.env.invalidate_all()

    def _with_receipt(self):
        order = self._order(quantity=10)
        self._resolve_product()
        self.line.import_purchase_line_id = order.order_line
        picking = order.picking_ids
        self.assertEqual(self.line.import_stock_move_id.picking_id, picking)
        return order, picking

    def test_the_document_counts_and_opens_its_receipt(self):
        _order, picking = self._with_receipt()
        self._fresh()

        document = self._as(self.document, self._storekeeper())

        self.assertEqual(document.import_picking_count, 1)
        self.assertEqual(document.import_picking_ids, picking)
        action = document.action_view_import_pickings()
        self.assertEqual(action["res_model"], "stock.picking")
        self.assertEqual(action["res_id"], picking.id)

    def test_the_suggested_receipt_counts_too(self):
        order = self._order(quantity=10)
        self._resolve_product()
        self.assertEqual(self.line.import_origin_state, "suggested")
        self._fresh()

        document = self._as(self.document, self._storekeeper())

        self.assertEqual(document.import_picking_ids, order.picking_ids)

    def test_the_receipt_created_from_the_document_counts(self):
        self._resolve_product()
        self.line.write({"import_origin_state": "no_order"})
        rows = self._rows(fiscal_document_id=self.document.id)
        action = rows.action_create_receipt()
        picking = self.env["stock.picking"].browse(action["res_id"])
        self._fresh()

        document = self._as(self.document, self._storekeeper())

        self.assertEqual(document.import_picking_ids, picking)

    def test_a_document_without_receipt_has_no_pickings(self):
        self._resolve_product()
        self._fresh()

        document = self._as(self.document, self._storekeeper())

        self.assertEqual(document.import_picking_count, 0)

    def test_the_document_opens_the_list_for_several_receipts(self):
        order, first = self._with_receipt()
        self._receive(order, 4, backorder=True)
        second = order.picking_ids.filtered(lambda pick: pick.state != "done")
        other = self.line.copy({"document_id": self.document.id})
        self._resolve_product(other)
        other.import_stock_move_id = second.move_ids
        self.line.import_stock_move_id = first.move_ids
        self._fresh()

        document = self._as(self.document, self._storekeeper())

        self.assertEqual(document.import_picking_count, 2)
        action = document.action_view_import_pickings()
        self.assertFalse(action.get("res_id"))
        self.assertEqual(sorted(action["domain"][0][2]), sorted((first | second).ids))

    def test_the_receipt_counts_and_opens_the_documents(self):
        _order, picking = self._with_receipt()
        self._fresh()

        receipt = self._as(picking, self._fiscal_user("button-fiscal-picking"))

        self.assertEqual(receipt.import_document_count, 1)
        action = receipt.action_view_import_documents()
        self.assertEqual(action["res_model"], "l10n_br_fiscal.document")
        self.assertEqual(action["res_id"], self.document.id)

    def test_the_count_of_a_list_of_receipts_is_read_once(self):
        _order, first = self._with_receipt()
        second = self._order(quantity=3).picking_ids
        self._fresh()

        pickings = (first | second).with_user(self._fiscal_user("button-list"))

        self.assertEqual(pickings.mapped("import_document_count"), [1, 0])

    def test_the_line_opens_the_receipt_before_the_order(self):
        order, picking = self._with_receipt()

        action = self.line.action_open_import_origin()

        self.assertEqual(action["res_model"], "stock.picking")
        self.assertEqual(action["res_id"], picking.id)
        self.line.import_stock_move_id = False
        self.assertEqual(
            self.line.action_open_import_origin()["res_model"], "purchase.order"
        )
        self.assertEqual(self.line.action_open_import_origin()["res_id"], order.id)

    def test_the_buttons_follow_the_groups(self):
        _order, picking = self._with_receipt()
        self._fresh()
        fiscal = self._fiscal_user("button-fiscal-view")
        storekeeper = self._storekeeper()
        name = "//button[@name='action_view_import_pickings']"

        arch = self._arch(self.document, fiscal)
        self.assertFalse(arch.xpath(name))
        self.assertFalse(arch.xpath("//field[@name='import_picking_count']"))
        self._read_form(self._as(self.document, fiscal), arch)
        arch = self._arch(self.document, storekeeper)
        self.assertTrue(arch.xpath(name))
        self._read_form(self._as(self.document, storekeeper), arch)
        # the receipt shows the document to the fiscal group only
        stock_only = self._fiscal_user("button-stock-only")
        stock_only.groups_id = [
            (3, self.env.ref("l10n_br_fiscal.group_user").id),
            (4, self.env.ref("stock.group_stock_user").id),
        ]
        arch = self._arch(picking, stock_only)
        self.assertFalse(arch.xpath("//button[@name='action_view_import_documents']"))
        self._read_form(self._as(picking, stock_only), arch)
        arch = self._arch(picking, storekeeper)
        self.assertTrue(arch.xpath("//button[@name='action_view_import_documents']"))
        self._read_form(self._as(picking, storekeeper), arch)
