# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    purchase_divergent = fields.Boolean(
        string="Divergent",
        compute="_compute_purchase_divergent",
        search="_search_purchase_divergent",
        help="Some line of the bill differs from its purchase order line or "
        "receipt by more than the tolerances of the company. It only warns: "
        "nothing is blocked.",
    )

    purchase_awaiting_receipt = fields.Boolean(
        string="Awaiting Receipt",
        compute="_compute_purchase_awaiting_receipt",
        help="Some line of the bill waits for the receipt of its order line. It "
        "only informs: nothing is blocked and it is not a divergence.",
    )

    @api.depends("invoice_line_ids.purchase_awaiting_receipt")
    def _compute_purchase_awaiting_receipt(self):
        for move in self:
            move.purchase_awaiting_receipt = any(
                move.invoice_line_ids.mapped("purchase_awaiting_receipt")
            )

    @api.depends("invoice_line_ids.purchase_divergent")
    def _compute_purchase_divergent(self):
        for move in self:
            move.purchase_divergent = any(
                move.invoice_line_ids.mapped("purchase_divergent")
            )

    @api.model
    def _search_purchase_divergent(self, operator, value):
        """Not stored (the receipts move after the bill is typed): the search
        looks at the bill lines linked to an order line, the only ones that
        can diverge, of the bills not paid yet, and answers with their bills."""
        if operator not in ("=", "!="):
            raise NotImplementedError("Only = and != are supported.")
        lines = self.env["account.move.line"].search(
            [
                ("purchase_line_id", "!=", False),
                ("display_type", "=", "product"),
                ("move_id.move_type", "in", ("in_invoice", "in_refund")),
                ("move_id.state", "!=", "cancel"),
                # a bill already paid is settled: the search does not read the
                # whole history of the purchases
                ("move_id.payment_state", "in", ("not_paid", "partial")),
            ]
        )
        divergent_ids = lines.filtered("purchase_divergent").move_id.ids
        if (operator == "=") == bool(value):
            return [("id", "in", divergent_ids)]
        return [("id", "not in", divergent_ids)]
