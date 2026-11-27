# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import date, datetime
from unittest import mock

from odoo.addons.l10n_br_fiscal_edi.tools import EdiLot

from .common import StockEdiCase


class TestLots(StockEdiCase):
    def _lots(self, quantity=4):
        """A tracked product ordered, and a document line that declares two lots."""
        self.product.tracking = "lot"
        self.order = self._order(quantity=quantity)
        self.move = self._moves(self.order)
        self.line.write({"quantity": quantity, "uom_id": self.unit.id})
        half = quantity / 2
        declared = [
            EdiLot("L-A", half, None, date(2027, 1, 10)),
            EdiLot("L-B", half, None, date(2027, 6, 30)),
        ]
        patcher = mock.patch.object(
            type(self.line), "_edi_get_lots", return_value=declared
        )
        patcher.start()
        self.addCleanup(patcher.stop)
        self._resolve_product()
        self.assertEqual(self.line.import_stock_move_id, self.move)
        return half

    def test_the_lots_of_the_document_are_proposed_not_validated(self):
        half = self._lots()
        picking = self.order.picking_ids
        self.assertTrue(picking.show_propose_lots_from_import)

        picking.action_propose_lots_from_import()

        lines = self.move.move_line_ids
        self.assertEqual(sorted(lines.mapped("lot_name")), ["L-A", "L-B"])
        self.assertEqual(sorted(lines.mapped("qty_done")), [half, half])
        if "expiration_date" in lines._fields:
            line_a = lines.filtered(lambda line: line.lot_name == "L-A")
            self.assertEqual(line_a.expiration_date, datetime(2027, 1, 10))
        # the receipt creates the lots on validation: nothing created now
        self.assertFalse(self.env["stock.lot"].search([("name", "in", ["L-A", "L-B"])]))
        self.assertEqual((picking.state, self.move.state), ("assigned", "assigned"))

    def test_an_existing_lot_is_used_by_its_id(self):
        self._lots()
        lot = self.env["stock.lot"].create(
            {
                "name": "L-A",
                "product_id": self.product.id,
                "company_id": self.move.company_id.id,
            }
        )

        self.move._propose_lots_from_import()

        lines = self.move.move_line_ids
        self.assertEqual(lines.filtered("lot_id").lot_id, lot)
        self.assertEqual(lines.filtered("lot_name").mapped("lot_name"), ["L-B"])

    def test_a_type_that_does_not_create_lots_gets_the_lot_now(self):
        self._lots()
        self.move.picking_type_id.use_create_lots = False
        self.move.picking_type_id.use_existing_lots = True

        self.move._propose_lots_from_import()

        self.assertEqual(
            sorted(self.move.move_line_ids.mapped("lot_id.name")), ["L-A", "L-B"]
        )
        self.assertEqual(self.order.picking_ids.state, "assigned")

    def test_a_product_without_lot_tracking_is_left_alone(self):
        self._lots()
        self.product.tracking = "none"
        before = self.move.move_line_ids

        self.assertTrue(self.move._propose_lots_from_import())

        self.assertEqual(self.move.move_line_ids, before)
        self.assertFalse(self.move.move_line_ids.lot_id)

    def test_a_receipt_already_filled_is_not_overwritten(self):
        self._lots()
        self.move.move_line_ids.write({"qty_done": 1.0})

        self.assertTrue(self.move._propose_lots_from_import())

        self.assertFalse(self.move.move_line_ids.lot_id)
        self.assertFalse(self.move.move_line_ids.lot_name)

    def test_open_receipt_proposes_the_lots_too(self):
        self._lots()

        self._rows(fiscal_document_id=self.document.id).action_open_receipt()

        self.assertEqual(
            sorted(self.move.move_line_ids.mapped("lot_name")), ["L-A", "L-B"]
        )

    def _user(self, login, *xmlids):
        company = self.company
        return self.env["res.users"].create(
            {
                "name": login,
                "login": login,
                "company_id": company.id,
                "company_ids": [(6, 0, company.ids)],
                "groups_id": [
                    (6, 0, [self.env.ref(x).id for x in ("base.group_user",) + xmlids])
                ],
            }
        )

    def test_a_storekeeper_without_fiscal_or_nfe_groups_proposes_the_lots(self):
        self._lots()
        user = self._user("storekeeper", "stock.group_stock_user")
        picking = self.order.picking_ids.with_user(user).with_context(
            allowed_company_ids=user.company_ids.ids
        )

        self.assertTrue(picking.show_propose_lots_from_import)
        picking.action_propose_lots_from_import()

        self.assertEqual(
            sorted(self.move.move_line_ids.mapped("lot_name")), ["L-A", "L-B"]
        )

    def test_a_buyer_without_fiscal_or_nfe_groups_opens_the_receipt_with_the_lots(
        self,
    ):
        self._lots()
        user = self._user(
            "buyer-open-receipt",
            "purchase.group_purchase_user",
            "stock.group_stock_user",
        )
        rows = self._rows(fiscal_document_id=self.document.id).with_user(user)

        action = rows.with_context(
            allowed_company_ids=user.company_ids.ids
        ).action_open_receipt()

        self.assertEqual(action["res_id"], self.order.picking_ids.id)
        self.assertEqual(
            sorted(self.move.move_line_ids.mapped("lot_name")), ["L-A", "L-B"]
        )
