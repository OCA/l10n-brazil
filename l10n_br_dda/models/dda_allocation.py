# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models

from ..constants import ALLOCATION_MODEL, DEBIT_MODEL


class DdaAllocation(models.Model):
    _name = ALLOCATION_MODEL
    _description = "DDA boleto allocation"
    _order = "debit_id, id"

    debit_id = fields.Many2one(
        comodel_name=DEBIT_MODEL, required=True, ondelete="cascade", index=True
    )
    company_id = fields.Many2one(related="debit_id.company_id", store=True)
    currency_id = fields.Many2one(related="debit_id.currency_id")
    move_line_id = fields.Many2one(
        comodel_name="account.move.line",
        string="Payable line",
        required=True,
        ondelete="restrict",
        index=True,
    )
    move_id = fields.Many2one(related="move_line_id.move_id", store=True)
    amount = fields.Monetary(
        currency_field="currency_id",
        help="Part of the boleto that settles this payable line (the open amount of "
        "the line when it was allocated).",
    )
    state = fields.Selection(related="debit_id.state")
