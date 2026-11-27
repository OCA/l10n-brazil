# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestBillDivergence(TransactionCase):
    """The vendor bill line against the order, the receipt and the tolerances.

    Read only: nothing is blocked, the line and the bill are marked.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.company = cls.env.ref("l10n_br_base.empresa_lucro_presumido")
        cls.env.user.company_ids |= cls.company
        cls.env = cls.env(
            context=dict(cls.env.context, allowed_company_ids=cls.company.ids)
        )
        cls.partner = cls.env.ref("l10n_br_base.res_partner_akretion")
        cls.product = cls.env.ref("product.product_product_12")
        cls.unit = cls.env.ref("uom.product_uom_unit")
        cls.dozen = cls.env.ref("uom.product_uom_dozen")

    def _order(self, quantity, price, uom=None):
        order = (
            self.env["purchase.order"]
            .with_company(self.company)
            .create(
                {
                    "partner_id": self.partner.id,
                    "company_id": self.company.id,
                    "order_line": [
                        Command.create(
                            {
                                "name": self.product.name,
                                "product_id": self.product.id,
                                "product_qty": quantity,
                                "product_uom": (uom or self.unit).id,
                                "price_unit": price,
                            }
                        )
                    ],
                }
            )
        )
        order.button_confirm()
        return order

    def _receive(self, order, quantity):
        picking = order.picking_ids
        picking.action_assign()
        picking.move_ids.quantity_done = quantity
        picking.with_context(cancel_backorder=True)._action_done()
        self.assertEqual(picking.state, "done")

    def _bill(self, order, quantity, price, uom=None):
        return (
            self.env["account.move"]
            .with_company(self.company)
            .create(
                {
                    "move_type": "in_invoice",
                    "partner_id": self.partner.id,
                    "company_id": self.company.id,
                    "invoice_date": "2026-11-18",
                    "invoice_line_ids": [
                        Command.create(
                            {
                                "product_id": self.product.id,
                                "quantity": quantity,
                                "price_unit": price,
                                "product_uom_id": (uom or self.unit).id,
                                "purchase_line_id": order.order_line.id,
                            }
                        )
                    ],
                }
            )
        )

    def test_the_bill_that_differs_from_the_order_and_the_receipt(self):
        order = self._order(10, 95.0)
        self._receive(order, 8)
        bill = self._bill(order, 10, 100.0)
        line = bill.invoice_line_ids
        self.assertEqual(line.purchase_ordered_qty, 10)
        self.assertEqual(line.purchase_received_qty, 8)
        self.assertEqual(line.purchase_price_unit, 95.0)
        self.assertEqual(line.purchase_qty_difference, 2)
        self.assertAlmostEqual(line.purchase_price_difference, 5.0)
        self.assertTrue(line.purchase_divergent)
        self.assertTrue(bill.purchase_divergent)
        found = self.env["account.move"].search([("purchase_divergent", "=", True)])
        self.assertIn(bill, found)
        rest = self.env["account.move"].search([("purchase_divergent", "=", False)])
        self.assertNotIn(bill, rest)
        # nothing is blocked
        bill.action_post()
        self.assertEqual(bill.state, "posted")

    def test_inside_the_tolerances_it_is_not_divergent(self):
        order = self._order(10, 95.0)
        self._receive(order, 8)
        bill = self._bill(order, 10, 100.0)
        self.assertTrue(bill.purchase_divergent)
        self.company.purchase_price_tolerance = 6.0
        self.company.purchase_quantity_tolerance = 30.0
        self.assertFalse(bill.invoice_line_ids.purchase_divergent)
        self.assertFalse(bill.purchase_divergent)
        # the price alone out of its tolerance is enough
        self.company.purchase_price_tolerance = 5.0
        self.assertTrue(bill.purchase_divergent)

    def test_a_bill_that_matches_is_not_divergent(self):
        order = self._order(10, 95.0)
        self._receive(order, 8)
        bill = self._bill(order, 8, 95.0)
        line = bill.invoice_line_ids
        self.assertEqual(line.purchase_qty_difference, 0)
        self.assertEqual(line.purchase_price_difference, 0)
        self.assertFalse(bill.purchase_divergent)

    def test_the_units_are_compared_in_the_unit_of_the_bill(self):
        """A dozen ordered and received, billed as 12 units at a twelfth."""
        order = self._order(1, 120.0, uom=self.dozen)
        # the receipt moves are in the unit of the product: 12 units
        self._receive(order, 12)
        bill = self._bill(order, 12, 10.0)
        line = bill.invoice_line_ids
        self.assertEqual(line.purchase_received_qty, 12)
        self.assertEqual(line.purchase_price_unit, 10.0)
        self.assertFalse(bill.purchase_divergent)

    def test_a_line_without_order_has_nothing_to_compare(self):
        bill = (
            self.env["account.move"]
            .with_company(self.company)
            .create(
                {
                    "move_type": "in_invoice",
                    "partner_id": self.partner.id,
                    "company_id": self.company.id,
                    "invoice_date": "2026-11-18",
                    "invoice_line_ids": [
                        Command.create(
                            {
                                "product_id": self.product.id,
                                "quantity": 3,
                                "price_unit": 10.0,
                            }
                        )
                    ],
                }
            )
        )
        line = bill.invoice_line_ids
        self.assertEqual(line.purchase_ordered_qty, 0)
        self.assertFalse(line.purchase_divergent)
        self.assertFalse(bill.purchase_divergent)

    def test_two_partial_bills_are_not_divergent(self):
        """The supplier bills the order in two parts, both right: neither of
        them is divergent, because each one is compared with what the other
        bills did not take yet and not with the whole receipt."""
        order = self._order(10, 95.0)
        self._receive(order, 10)
        first = self._bill(order, 5, 95.0)
        second = self._bill(order, 5, 95.0)
        for bill in (first, second):
            self.assertEqual(bill.invoice_line_ids.purchase_qty_difference, 0)
            self.assertFalse(bill.purchase_divergent)
        # a bill that takes what was already billed is divergent
        third = self._bill(order, 5, 95.0)
        self.assertEqual(third.invoice_line_ids.purchase_qty_difference, 5)
        self.assertTrue(third.purchase_divergent)
        # the bill that is cancelled does not take anything
        second.button_cancel()
        third.invoice_line_ids.invalidate_recordset()
        self.assertEqual(third.invoice_line_ids.purchase_qty_difference, 0)
        self.assertFalse(third.purchase_divergent)

    def test_the_lines_of_one_bill_for_the_same_order_line_count_together(self):
        """The supplier splits the item by lot in two lines of the same bill: the
        bill is compared as a whole with the receipt."""
        order = self._order(10, 95.0)
        self._receive(order, 10)
        bill = self._bill(order, 5, 95.0)
        bill.write(
            {
                "invoice_line_ids": [
                    Command.create(
                        {
                            "product_id": self.product.id,
                            "quantity": 5,
                            "price_unit": 95.0,
                            "product_uom_id": self.unit.id,
                            "purchase_line_id": order.order_line.id,
                        }
                    )
                ]
            }
        )
        self.assertEqual(len(bill.invoice_line_ids), 2)
        self.assertEqual(
            bill.invoice_line_ids.mapped("purchase_qty_difference"), [0, 0]
        )
        self.assertFalse(bill.purchase_divergent)
