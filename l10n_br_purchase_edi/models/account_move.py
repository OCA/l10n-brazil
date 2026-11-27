# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from collections import defaultdict

from odoo import _, api, models
from odoo.tools import float_compare


class AccountMove(models.Model):
    _inherit = "account.move"

    @api.model
    def import_fiscal_document(
        self, fiscal_document, move_id=None, move_type="in_invoice"
    ):
        move_form = super().import_fiscal_document(
            fiscal_document, move_id=move_id, move_type=move_type
        )
        self.browse(move_form.id)._link_purchase_lines_from_import()
        return move_form

    def _link_purchase_lines_from_import(self):
        """Link the bill lines to the order lines resolved on the lines of the
        imported document, so the order counts the quantity as invoiced.

        An order line takes more than one bill line (the supplier splits the
        same item by lot) as long as the sum fits in what is left of it, after
        the other bills that are not cancelled. A line that would pass it
        stays unlinked and the bill says so.
        """
        self.ensure_one()
        if self.move_type != "in_invoice":
            return
        taken = defaultdict(float)
        not_linked = []
        for line in self.invoice_line_ids.filtered(
            lambda aml: aml.display_type == "product"
        ):
            fiscal_line = line.fiscal_document_line_id
            order_line = fiscal_line.import_purchase_line_id.sudo()
            if fiscal_line.import_origin_state != "resolved" or not order_line:
                continue
            quantity = fiscal_line._import_claimed_quantity(order_line)
            balance = (
                order_line.product_qty
                + order_line._import_quantity_tolerance()
                - order_line._quantity_billed_elsewhere(self)
            )
            if (
                float_compare(
                    taken[order_line] + quantity,
                    balance,
                    precision_rounding=order_line.product_uom.rounding,
                )
                > 0
            ):
                not_linked.append(line.name)
                continue
            line.purchase_line_id = order_line
            taken[order_line] += quantity
        if taken and not self.invoice_origin:
            self.invoice_origin = ", ".join(
                self.env["purchase.order.line"].concat(*taken).order_id.mapped("name")
            )
        if not_linked:
            self.message_post(
                body=_(
                    "Not linked to the purchase order, the quantity does not fit "
                    "in what is left of the order line: %s",
                    ", ".join(not_linked),
                )
            )
