# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"
    _rec_names_search = ["name", "order_id.name"]

    def name_get(self):
        # two lines of different orders share the description: show the order
        result = []
        for line in self.sudo():
            name = line.name or line.product_id.display_name or ""
            if line.order_id:
                name = f"{line.order_id.name}: {name}"
            result.append((line.id, name))
        return result

    def _import_quantity_tolerance(self):
        """Quantity above the ordered one that the bills may still take."""
        self.ensure_one()
        return 0.0

    def _quantity_billed_elsewhere(self, move=None):
        """Quantity of the line on the bills not cancelled (credit notes take
        from it), in the order unit, leaving out the lines of ``move``."""
        self.ensure_one()
        total = 0.0
        for bill_line in self.sudo().invoice_lines:
            bill = bill_line.move_id
            if bill == move or bill.state == "cancel":
                continue
            quantity = bill_line.product_uom_id._compute_quantity(
                bill_line.quantity, self.product_uom, raise_if_failure=False
            )
            total += -quantity if bill.move_type == "in_refund" else quantity
        return total

    def _find_by_import_reference(self, company, partner, order_name, item, product):
        """The line of a confirmed order that the supplier referred to (xPed and
        nItemPed); empty when it does not identify exactly one line."""
        none = self.browse()
        if not order_name:
            return none
        # xPed is a Char(15): a longer order name arrives truncated
        truncated = len(order_name) >= 15
        orders = self.env["purchase.order"].search(
            [
                ("name", "=like" if truncated else "=", order_name + truncated * "%"),
                ("company_id", "=", company.id),
                ("state", "in", ("purchase", "done")),
                ("partner_id.commercial_partner_id", "=", partner.id),
            ]
        )
        orders = orders.filtered(lambda order: order.name[:15] == order_name[:15])
        if len(orders) != 1:
            return none
        # nItemPed is the 1-based position of the line in the order
        order_lines = orders.order_line.filtered(
            lambda pol: not pol.display_type
        ).sorted(lambda pol: (pol.sequence, pol.id))
        digits = "".join(char for char in (item or "") if char.isdigit())
        if digits:
            position = int(digits)
            candidates = order_lines[position - 1 : position] if position else none
        else:
            candidates = order_lines
        if product is not None:
            candidates = candidates.filtered(lambda pol: pol.product_id == product)
        else:
            candidates = candidates.filtered("product_id")
        return candidates if len(candidates) == 1 else none
