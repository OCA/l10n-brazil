# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    def _suggest_origin_on_imported_lines(self):
        result = super()._suggest_origin_on_imported_lines()
        # the order created from the request waited for its approval: the
        # person decided it when creating it, so it is resolved now
        orders = self.filtered(lambda order: order.state in ("purchase", "done"))
        self.env["l10n_br_fiscal.document.line"].sudo().search(
            [
                ("import_origin_state", "=", "suggested"),
                ("import_request_line_id", "!=", False),
                ("import_purchase_line_id.order_id", "in", orders.ids),
            ]
        ).write({"import_origin_state": "resolved"})
        return result
