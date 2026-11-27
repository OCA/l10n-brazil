# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    purchase_ordered_qty = fields.Float(
        string="Ordered Quantity",
        compute="_compute_purchase_comparison",
        digits="Product Unit of Measure",
        help="Quantity of the purchase order line this bill line is linked "
        "to, in the unit of the bill line.",
    )
    purchase_received_qty = fields.Float(
        string="Received Quantity",
        compute="_compute_purchase_comparison",
        digits="Product Unit of Measure",
        help="Quantity received for the order line (done receipts, less the "
        "returns), in the unit of the bill line.",
    )
    purchase_price_unit = fields.Float(
        string="Order Unit Price",
        compute="_compute_purchase_comparison",
        digits="Product Price",
        help="Unit price of the order line, in the unit and the currency of "
        "the bill line.",
    )
    purchase_qty_difference = fields.Float(
        string="Quantity Difference",
        compute="_compute_purchase_comparison",
        digits="Product Unit of Measure",
        help="Billed quantity minus the received quantity that the other bills "
        "did not take yet (the lines of this same bill for the order line "
        "count together).",
    )
    purchase_price_difference = fields.Float(
        string="Price Difference",
        compute="_compute_purchase_comparison",
        digits="Product Price",
        help="Unit price of the bill minus the unit price of the order.",
    )
    purchase_awaiting_receipt = fields.Boolean(
        string="Awaiting Receipt",
        compute="_compute_purchase_comparison",
        help="The bill line is for an item that goes to the stock and nothing was "
        "received yet. It only informs: it is not a divergence.",
    )
    purchase_divergent = fields.Boolean(
        string="Divergent",
        compute="_compute_purchase_comparison",
        help="The bill line differs from the order and the receipt by more "
        "than the tolerances of the company. It only warns: nothing is "
        "blocked.",
    )

    @api.depends(
        "purchase_line_id.product_qty",
        "purchase_line_id.product_uom",
        "purchase_line_id.qty_received",
        "purchase_line_id.price_unit",
        "purchase_line_id.invoice_lines.quantity",
        "purchase_line_id.invoice_lines.product_uom_id",
        "purchase_line_id.invoice_lines.move_id.state",
        "move_id.invoice_line_ids.purchase_line_id",
        "move_id.invoice_line_ids.quantity",
        "move_id.move_type",
        "move_id.invoice_date",
        "quantity",
        "price_unit",
        "product_uom_id",
        "currency_id",
        "company_id.purchase_price_tolerance",
        "company_id.purchase_quantity_tolerance",
    )
    def _compute_purchase_comparison(self):
        """Compare the bill line with its order line and receipts. Not stored:
        the receipts move after the bill is typed."""
        for line in self:
            values = {
                "ordered": 0.0,
                "received": 0.0,
                "price": 0.0,
                "qty_difference": 0.0,
                "price_difference": 0.0,
                "divergent": False,
                "awaiting": False,
            }
            order_line = line.purchase_line_id
            if order_line and line.move_id.is_purchase_document(include_receipts=True):
                uom = line.product_uom_id or order_line.product_uom
                # the lines of this bill for the order line (the supplier
                # splitting the item by lot) count together
                billed = sum(
                    (other.product_uom_id or uom)._compute_quantity(
                        other.quantity, uom, raise_if_failure=False
                    )
                    for other in line.move_id.invoice_line_ids
                    if other.purchase_line_id == order_line
                )
                values = order_line._import_compare(
                    billed or line.quantity,
                    uom,
                    line.price_unit,
                    line.currency_id,
                    line.move_id.invoice_date or fields.Date.context_today(line),
                    line.move_id,
                )
            line.purchase_ordered_qty = values["ordered"]
            line.purchase_received_qty = values["received"]
            line.purchase_price_unit = values["price"]
            line.purchase_qty_difference = values["qty_difference"]
            line.purchase_price_difference = values["price_difference"]
            line.purchase_divergent = values["divergent"]
            line.purchase_awaiting_receipt = values["awaiting"]
