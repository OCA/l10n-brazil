# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models
from odoo.tools import float_compare


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    def _import_receipt_moves(self):
        """The receipt moves of the line that an imported document line can
        point to: the incoming ones that are not cancelled (a return is never
        an origin). The done ones count only while what was received is not yet
        invoiced; otherwise the receipt still to come is the candidate."""
        self.ensure_one()
        line = self.sudo()
        moves = line.move_ids.filtered(
            lambda move: move.picking_type_id.code == "incoming"
            and move.state != "cancel"
        )
        done = moves.filtered(lambda move: move.state == "done")
        not_invoiced = float_compare(
            line.qty_received - line.qty_invoiced,
            0.0,
            precision_rounding=line.product_uom.rounding,
        )
        return done if done and not_invoiced > 0 else moves - done

    def _import_billed_elsewhere(self, moves):
        """Quantity of the line on the bills not cancelled (credit notes take
        from it), in the order unit, leaving out the bills in ``moves``."""
        self.ensure_one()
        total = 0.0
        for bill_line in self.sudo().invoice_lines:
            bill = bill_line.move_id
            if bill in moves or bill.state == "cancel":
                continue
            quantity = bill_line.product_uom_id._compute_quantity(
                bill_line.quantity, self.product_uom, raise_if_failure=False
            )
            total += -quantity if bill.move_type == "in_refund" else quantity
        return total

    def _import_compare(self, quantity, uom, price_unit, currency, date, moves):
        """Compare what a document or a bill line says with the order and the
        receipts, in the unit and the currency of that line.

        ``quantity`` is compared with what is still to be billed: the received
        quantity less what the other bills (not in ``moves``) already took.
        Nothing is blocked, the result only marks the line.
        """
        self.ensure_one()
        order_line = self.sudo()
        order_uom = order_line.product_uom
        if not uom or uom.category_id != order_uom.category_id:
            uom = order_uom
        ordered = order_uom._compute_quantity(order_line.product_qty, uom)
        received = order_uom._compute_quantity(order_line.qty_received, uom)
        price = order_uom._compute_price(order_line.price_unit, uom)
        if order_line.currency_id != currency:
            price = order_line.currency_id._convert(
                price, currency, order_line.company_id, date
            )
        elsewhere = order_uom._compute_quantity(
            order_line._import_billed_elsewhere(moves), uom
        )
        price_difference = price_unit - price
        company = order_line.company_id
        # nothing received yet for an item that goes to the stock: the bill waits
        # for the receipt, which is not a divergence
        awaiting = (
            order_line.product_id.type
            in (
                "product",
                "consu",
            )
            and not float_compare(received, 0.0, precision_rounding=uom.rounding) > 0
        )
        qty_difference = 0.0 if awaiting else quantity - (received - elsewhere)
        quantity_tolerance = abs(received) * company.purchase_quantity_tolerance / 100
        ordered_tolerance = abs(ordered) * company.purchase_quantity_tolerance / 100
        price_tolerance = abs(price) * company.purchase_price_tolerance / 100
        digits = self.env["decimal.precision"].precision_get("Product Price")
        # the note takes more than what is left of the order
        over_ordered = (
            float_compare(
                quantity + elsewhere - ordered,
                ordered_tolerance,
                precision_rounding=uom.rounding,
            )
            > 0
        )
        divergent = (
            over_ordered
            or float_compare(
                abs(qty_difference), quantity_tolerance, precision_rounding=uom.rounding
            )
            > 0
            or float_compare(
                abs(price_difference), price_tolerance, precision_digits=digits
            )
            > 0
        )
        return {
            "ordered": ordered,
            "received": received,
            "price": price,
            "qty_difference": qty_difference,
            "price_difference": price_difference,
            "divergent": divergent,
            "awaiting": awaiting,
        }
