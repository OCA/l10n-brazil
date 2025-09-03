# Copyright 2025 - TODAY, Cristiano Mafra Junior <cristiano.mafra@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class AccountMoveReversal(models.TransientModel):
    _inherit = "account.move.reversal"

    payment_mode_id = fields.Many2one(
        comodel_name="account.payment.mode",
        string="Payment Mode",
    )

    def default_get(self, fields_list):
        res = super().default_get(fields_list)

        active_ids = self.env.context.get("active_ids", [])
        if active_ids:
            invoice = self.env["account.move"].browse(active_ids[0])
            if invoice.payment_mode_id:
                res["payment_mode_id"] = invoice.payment_mode_id.id

        return res

    def reverse_moves(self):
        self.ensure_one()
        return super(
            AccountMoveReversal,
            self.with_context(payment_mode_id=self.payment_mode_id.id),
        ).reverse_moves()
