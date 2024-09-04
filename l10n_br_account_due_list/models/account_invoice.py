# Copyright (C) 2021 - TODAY Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models


class AccountInvoice(models.Model):
    _inherit = "account.move"

    financial_move_line_ids = fields.Many2many(
        comodel_name="account.move.line",
        relation="account_invoice_account_financial_move_line_rel",
        compute="_compute_financial",
        store=True,
        string="Financial Move Lines",
    )

    payment_move_line_ids = fields.Many2many(
        "account.move.line",
        string="Payment Move Lines",
        compute="_compute_payments",
        store=True,
    )

    @api.depends("line_ids", "state")
    def _compute_financial(self):
        for move in self:
            lines = move.line_ids.filtered(
                lambda line: line.account_id.account_type
                in ("asset_receivable", "liability_payable")
            )
            move.financial_move_line_ids = lines.sorted()

    @api.depends("line_ids.amount_residual")
    def _compute_payments(self):
        for move in self:
            (
                invoice_partials,
                exchange_diff_moves,
            ) = move._get_reconciled_invoices_partials()
            move.payment_move_line_ids = [partial[2].id for partial in invoice_partials]
