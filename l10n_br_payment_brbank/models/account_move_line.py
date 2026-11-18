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

    def _reconcile_post_hook(self, data):
        res = super()._reconcile_post_hook(data)
        self._brbank_write_off_paid_installments()
        return res

    def _brbank_write_off_paid_installments(self):
        """An installment paid by other means (cash, a Pix to the company key)
        must not stay payable by boleto. A boleto paid at the bank is `done`
        before its own payment reconciles, so it is not touched here."""
        installments = self.filtered(
            lambda line: line.display_type == "payment_term" and line.reconciled
        )
        if not installments:
            return
        self.env["payment.transaction"].sudo().search(
            [
                ("move_line_id", "in", installments.ids),
                ("provider_code", "=", BRBANK),
                ("state", "in", ("draft", "authorized")),
            ]
        )._brbank_queue_write_off(_("Installment paid by other means."))
