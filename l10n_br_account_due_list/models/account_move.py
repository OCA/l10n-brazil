# Copyright (C) 2021 - TODAY Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    due_line_ids = fields.One2many(
        comodel_name="account.move.line",
        inverse_name="move_id",
        string="Installments",
        readonly=True,
        domain=[("display_type", "=", "payment_term")],
    )

    payment_move_line_ids = fields.Many2many(
        comodel_name="account.move.line",
        string="Payment Lines",
        compute="_compute_payment_lines",
        readonly=True,
        help="Payment journal items reconciled with this invoice.",
    )

    @api.depends(
        "line_ids.matched_debit_ids",
        "line_ids.matched_credit_ids",
        "line_ids.amount_residual",
    )
    def _compute_payment_lines(self):
        """
        Compute the payment lines by finding all journal items that have been
        reconciled with the receivable/payable lines of this invoice.
        """
        for move in self:
            (
                invoice_partials,
                exchange_diff_moves,
            ) = move._get_reconciled_invoices_partials()
            move.payment_move_line_ids = [partial[2].id for partial in invoice_partials]
