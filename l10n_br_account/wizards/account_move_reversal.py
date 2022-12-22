# Copyright (C) 2013  Florian da Costa - Akretion
# Copyright (C) 2021  Luis Felipe Miléo - KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html


from odoo import fields, models


class AccountMoveReversal(models.TransientModel):
    _inherit = "account.move.reversal"

    force_fiscal_operation_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.operation", string="Force Fiscal Operation"
    )

    def reverse_moves(self):
        self.ensure_one()
        return super(
            AccountMoveReversal,
            self.with_context(
                force_fiscal_operation_id=self.force_fiscal_operation_id.id
            ),
        ).reverse_moves()
