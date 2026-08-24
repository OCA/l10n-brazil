# Copyright 2026 - TODAY Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, fields, models
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = "account.move"

    can_renegotiate_installments = fields.Boolean(
        compute="_compute_can_renegotiate_installments",
        help="Technical field to determine if installment renegotiation is available",
    )

    def _compute_can_renegotiate_installments(self):
        """
        Determine if the invoice can have its installments renegotiated.
        Conditions:
        - Invoice is posted
        - Invoice is a customer invoice or vendor bill
        - Has at least one unreconciled payment_term line
        """
        for move in self:
            move.can_renegotiate_installments = (
                move.state == "posted"
                and move.is_invoice(include_receipts=True)
                and any(
                    line.display_type == "payment_term" and not line.reconciled
                    for line in move.line_ids
                )
            )

    def action_renegotiate_installments(self):
        """
        Open the installment renegotiation wizard.
        Only available for posted invoices with unreconciled payment_term lines.
        """
        self.ensure_one()

        # Security check
        if not self.env.user.has_group("account.group_account_manager"):
            raise UserError(
                _(
                    "Only users with 'Billing Administrator' rights can "
                    "renegotiate installments."
                )
            )

        if self.state != "posted":
            raise UserError(
                _("You can only renegotiate installments on posted invoices.")
            )

        if not self.is_invoice(include_receipts=True):
            raise UserError(
                _("Installment renegotiation is only available for invoices and bills.")
            )

        unreconciled_payment_lines = self.line_ids.filtered(
            lambda line: line.display_type == "payment_term" and not line.reconciled
        )

        if not unreconciled_payment_lines:
            raise UserError(
                _(
                    "There are no unreconciled payment term lines to renegotiate. "
                    "All installments have been paid or reconciled."
                )
            )

        # Create wizard with pre-populated installment lines
        wizard = self.env["account.installment.renegotiation.wizard"].create(
            {
                "move_id": self.id,
            }
        )

        return {
            "name": _("Renegotiate Installments"),
            "type": "ir.actions.act_window",
            "res_model": "account.installment.renegotiation.wizard",
            "view_mode": "form",
            "res_id": wizard.id,
            "target": "new",
            "context": self.env.context,
        }

    def _get_installment_renegotiation_message(self, old_lines_data, new_lines_data):
        currency = self.currency_id

        def format_line(line_data):
            base = _("%(date)s: %(amount)s") % {
                "date": line_data["date_maturity"],
                "amount": currency.format(abs(line_data["amount_currency"])),
            }
            # Append payment mode to the log if available
            if line_data.get("payment_mode"):
                base += f" ({line_data['payment_mode']})"
            return base

        old_summary = "<br/>".join(format_line(line) for line in old_lines_data)
        new_summary = "<br/>".join(format_line(line) for line in new_lines_data)

        message = _(
            "<p><strong>Payment Installments Renegotiated</strong></p>"
            "<p><strong>Previous installments:</strong><br/>%(old)s</p>"
            "<p><strong>New installments:</strong><br/>%(new)s</p>"
        ) % {
            "old": old_summary,
            "new": new_summary,
        }

        return message
