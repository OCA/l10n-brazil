# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, fields, models

from .payment_provider import BRBANK


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    brbank_boleto_action_available = fields.Boolean(
        compute="_compute_brbank_boleto_action_available"
    )

    def _brbank_boleto_transaction(self):
        """The boleto of this installment, as the system: the live one, else the
        last one issued (written off, refused or never registered)."""
        self.ensure_one()
        transactions = self.env["payment.transaction"].sudo()
        if not self._origin:
            return transactions
        transactions = transactions.search(
            [("move_line_id", "=", self._origin.id), ("provider_code", "=", BRBANK)],
            order="id desc",
        )
        live = transactions.filtered(lambda t: t._brbank_is_live())
        return live[:1] or transactions[:1]

    def _brbank_can_issue_boleto(self):
        """An open installment of a posted invoice charged through brbank."""
        self.ensure_one()
        move = self.move_id
        provider = move.payment_mode_id.payment_provider_id.sudo()
        return bool(
            self._origin
            and self.display_type == "payment_term"
            and not self.reconciled
            and move.state == "posted"
            and move.move_type == "out_invoice"
            and provider.code == BRBANK
            and provider.state != "disabled"
        )

    def _compute_brbank_boleto_action_available(self):
        Action = self.env["l10n_br.boleto.action"]
        for line in self:
            line.brbank_boleto_action_available = bool(
                not line.reconciled
                and Action._available_actions(line._brbank_boleto_transaction(), line)
            )

    def action_brbank_boleto_actions(self):
        self.ensure_one()
        return self.env["l10n_br.boleto.action"]._open_for(
            self._brbank_boleto_transaction(), self
        )

    def _brbank_set_due_date(self, new_date):
        """Move the installment; `invoice_date_due` stays as core defines it, the
        due date of the last installment."""
        self.ensure_one()
        no_sync = self.with_context(skip_invoice_sync=True)
        no_sync.date_maturity = new_date
        invoice = no_sync.move_id
        invoice.invoice_date_due = max(
            invoice.due_line_ids.filtered("date_maturity").mapped("date_maturity")
        )

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
