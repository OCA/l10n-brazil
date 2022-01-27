# Copyright (C) 2021 - TODAY Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models


class AccountInvoice(models.Model):
    _inherit = "account.move"

    financial_move_line_ids = fields.One2many(
        comodel_name="account.move.line",
        inverse_name="move_id",
        string="Financial Move Lines",
        copy=False,
        readonly=True,
        states={"draft": [("readonly", False)]},
        domain="[('account_id.user_type_id.type', 'in', ('receivable', 'payable'))]",
    )

    payment_move_line_ids = fields.One2many(
        comodel_name="account.payment",
        inverse_name="move_id",
        string="Payment Move Lines",
    )
