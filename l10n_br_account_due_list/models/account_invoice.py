# Copyright (C) 2021 - TODAY Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    financial_move_line_ids = fields.Many2many(
        comodel_name="account.move.line",
        relation="account_invoice_account_financial_move_line_rel",
        compute="_compute_financial",
        store=True,
        string="Financial Move Lines",
    )

    @api.depends("move_id.line_ids", "move_id.state")
    def _compute_financial(self):
        for invoice in self:
            lines = invoice.move_id.line_ids.filtered(
                lambda l: l.account_id == invoice.account_id
                and l.account_id.internal_type in ("receivable", "payable")
            )
            invoice.financial_move_line_ids = lines.sorted()
