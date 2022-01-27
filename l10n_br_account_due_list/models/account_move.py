# Copyright (C) 2021 - TODAY Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models


class AccountInvoice(models.Model):
    _inherit = "account.move"

    financial_move_line_ids = fields.One2many(
        comodel_name="account.move.line",
        inverse_name="move_id",
        string="Financial Move Lines",
        readonly=True,
        domain="[('account_id.user_type_id.type', 'in', ('receivable', 'payable'))]",
    )

    payment_move_line_ids = fields.Many2many(
        comodel_name="account.move.line",
        relation="account_invoice_account_payment_move_line_rel",
        string="Payment Move Lines",
        compute="_compute_payments",
        store=True,
    )

    @api.depends("line_ids.amount_residual")
    def _compute_payments(self):
        for move in self:
            move.payment_move_line_ids = [
                aml.id
                for partial, amount, aml in move._get_reconciled_invoices_partials()
            ]
