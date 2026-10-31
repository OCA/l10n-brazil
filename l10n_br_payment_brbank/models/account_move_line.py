# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, fields, models
from odoo.exceptions import UserError

from .payment_provider import BRBANK


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    brbank_instruction_available = fields.Boolean(
        compute="_compute_brbank_instruction_available"
    )

    def _brbank_live_transaction(self):
        """The registered boleto of this open installment, as the system."""
        self.ensure_one()
        transactions = self.env["payment.transaction"].sudo()
        if not self._origin or self.reconciled:
            return transactions
        return transactions.search(
            [
                ("move_line_id", "=", self._origin.id),
                ("provider_code", "=", BRBANK),
                ("state", "=", "authorized"),
                ("provider_reference", "!=", False),
            ],
            limit=1,
        )

    def _compute_brbank_instruction_available(self):
        for line in self:
            transaction = line._brbank_live_transaction()
            line.brbank_instruction_available = bool(
                transaction and transaction._brbank_available_commands()
            )

    def action_brbank_new_instruction(self):
        self.ensure_one()
        transaction = self._brbank_live_transaction()
        if not transaction:
            raise UserError(_("This installment has no registered boleto."))
        return transaction.action_brbank_new_instruction()
