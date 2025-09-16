# Copyright (C) 2013  Florian da Costa - Akretion
# Copyright (C) 2021  Luis Felipe Miléo - KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html


from odoo import api, fields, models


class AccountMoveReversal(models.TransientModel):
    _inherit = "account.move.reversal"

    force_fiscal_operation_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.operation", string="Force Fiscal Operation"
    )

    force_fiscal_operation_journal_id = fields.Many2one(
        related="force_fiscal_operation_id.journal_id",
    )

    def reverse_moves(self):
        self.ensure_one()
        return super(
            AccountMoveReversal,
            self.with_context(
                force_fiscal_operation_id=self.force_fiscal_operation_id.id
            ),
        ).reverse_moves()

    @api.depends("move_ids", "force_fiscal_operation_id")
    def _compute_journal_id(self):
        for record in self:
            if record.force_fiscal_operation_id.journal_id:
                record.journal_id = record.force_fiscal_operation_id.journal_id
            else:
                return super()._compute_journal_id()
