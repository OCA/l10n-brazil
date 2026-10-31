# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, models
from odoo.exceptions import UserError

from .payment_provider import BRBANK


class AccountMove(models.Model):
    _inherit = "account.move"

    def _compute_invoice_date_due(self):
        """Core reads the payment term: an extended boleto would go back on the
        next reconciliation."""
        res = super()._compute_invoice_date_due()
        for move in self.filtered(lambda m: m.state == "posted" and m.transaction_ids):
            dates = move.due_line_ids.filtered("date_maturity").mapped("date_maturity")
            if dates:
                move.invoice_date_due = max(dates)
        return res

    def generate_boletos(self):
        provider = self.payment_mode_id.payment_provider_id.sudo()
        if provider.code == BRBANK:
            self._brbank_create_boletos()
        return super().generate_boletos()

    def _brbank_create_boletos(self):
        """Issue one bank title per open installment without a live one."""
        self.ensure_one()
        provider = self.payment_mode_id.payment_provider_id.sudo()
        if provider.state == "disabled":
            raise UserError(
                _(
                    "The payment provider %s of the payment mode is disabled.",
                    provider.name,
                )
            )
        transactions = self.env["payment.transaction"].sudo()
        installments = self.due_line_ids.sorted(
            lambda line: (line.date_maturity, line.id)
        )
        for index, installment in enumerate(installments, start=1):
            if installment.reconciled or self._boleto_get_active_transactions(
                installment
            ):
                continue
            transaction = transactions.create(
                self._brbank_prepare_transaction_values(installment, index)
            )
            transaction._brbank_register()
            transactions |= transaction
        return transactions

    def _brbank_prepare_transaction_values(self, installment, index):
        """Values of the transaction that charges `installment`, with stable keys."""
        provider = self.payment_mode_id.payment_provider_id.sudo()
        mode = self.payment_mode_id
        attempt = len(
            self.transaction_ids.filtered(
                lambda t: t.move_line_id == installment and t.provider_code == BRBANK
            )
        )
        Transaction = self.env["payment.transaction"]
        return {
            "reference": Transaction._compute_reference(
                provider.code, prefix=f"{self.name}-{index}"
            ),
            "provider_id": provider.id,
            "payment_method_id": provider._brbank_payment_method().id,
            "partner_id": self.partner_id.commercial_partner_id.id,
            "operation": "offline",
            "is_boleto_payment": True,
            "amount": abs(installment.amount_residual_currency),
            "currency_id": self.currency_id.id,
            "due_date": installment.date_maturity,
            "boleto_penalty": mode.payment_boleto_penalty or 0.0,
            "boleto_interest": mode.payment_boleto_interest or 0.0,
            "boleto_instructions": mode.payment_boleto_instructions or "",
            "invoice_ids": [(6, 0, self.ids)],
            "move_line_id": installment.id,
            "brbank_idempotency_key": Transaction._brbank_new_idempotency_key(
                f"aml{installment.id}-{attempt}"
            ),
            "brbank_seu_numero": f"{installment.id}{attempt:02d}",
        }
