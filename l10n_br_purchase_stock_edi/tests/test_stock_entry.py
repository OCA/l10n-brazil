# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.exceptions import UserError

from .common import StockEdiCase


class TestStockEntry(StockEdiCase):
    def _no_order(self):
        self._resolve_product()
        note = self._rows(fiscal_document_id=self.document.id)
        note.action_no_order()
        return note

    def _user(self, login, *group_xmlids):
        groups = [self.env.ref(xmlid).id for xmlid in group_xmlids]
        return self.env["res.users"].create(
            {
                "name": "Buyer",
                "login": login,
                "company_ids": [(6, 0, self.company.ids)],
                "company_id": self.company.id,
                "groups_id": [(6, 0, groups)],
            }
        )

    def test_without_order_a_stockable_product_needs_the_stock_entry(self):
        self._no_order()

        with self.assertRaisesRegex(UserError, "no order and no receipt"):
            self.document.action_generate_invoice()

    def test_a_consumable_goes_on_without_order_and_receipt(self):
        self.product.detailed_type = "consu"
        self._no_order()

        action = self.document.action_generate_invoice()

        self.assertTrue(action["res_id"])

    def test_the_receipt_created_from_the_document_unlocks_it(self):
        note = self._no_order()

        action = note.action_create_receipt()

        picking = self.env["stock.picking"].browse(action["res_id"])
        move = picking.move_ids
        self.assertEqual(picking.picking_type_id.code, "incoming")
        self.assertEqual(picking.state, "assigned")
        self.assertEqual((move.product_id, move.product_uom), (self.product, self.unit))
        self.assertEqual(move.product_uom_qty, self.line.quantity)
        self.assertEqual(move.price_unit, self.line.price_unit)
        self.assertEqual(self.line.import_stock_move_id, move)
        self.assertEqual(self.line.import_origin_state, "no_order")
        self.assertTrue(self.document.action_generate_invoice())

    def test_the_receipt_is_for_stockable_lines_without_order_and_receipt(self):
        self._resolve_product()
        note = self._rows(fiscal_document_id=self.document.id)
        with self.assertRaisesRegex(UserError, "without order"):
            note.action_create_receipt()

        note.action_no_order()
        note.action_create_receipt()
        with self.assertRaisesRegex(UserError, "without order"):
            self._rows(fiscal_document_id=self.document.id).action_create_receipt()

    def test_the_receipt_does_not_convert_a_unit_nobody_confirmed(self):
        note = self._no_order()
        self.line.write(
            {"partner_uom_code": "XYZ", "uom_id": False, "import_uom_id": False}
        )

        with self.assertRaisesRegex(UserError, "was not confirmed"):
            note.action_create_receipt()

    def test_only_a_manager_marks_no_stock_entry(self):
        self._no_order()
        buyer = self._user("buyer", "purchase.group_purchase_user")
        manager = self._user("manager", "purchase.group_purchase_manager")
        rows = self._rows(fiscal_document_id=self.document.id)

        with self.assertRaisesRegex(UserError, "Only a purchase manager"):
            rows.with_user(buyer).with_context(
                allowed_company_ids=buyer.company_ids.ids
            ).action_no_stock_entry()
        self.assertFalse(self.line.sudo().import_no_stock_entry)

        rows.with_user(manager).with_context(
            allowed_company_ids=manager.company_ids.ids
        ).action_no_stock_entry()

        self.assertTrue(self.line.sudo().import_no_stock_entry)
        self.assertTrue(self.document.action_generate_invoice())

    def test_creating_the_receipt_does_not_write_on_the_partner(self):
        note = self._no_order()
        before = (self.supplier.name, self.supplier.write_date)

        action = note.action_create_receipt()

        picking = self.env["stock.picking"].browse(action["res_id"])
        self.assertEqual(picking.partner_id, self.supplier)
        self.assertEqual((self.supplier.name, self.supplier.write_date), before)
