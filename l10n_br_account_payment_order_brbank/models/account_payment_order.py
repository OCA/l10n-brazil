# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import AccessError, UserError


class AccountPaymentOrder(models.Model):
    _inherit = "account.payment.order"
    _api_second_factor_methods = ("_brbank_authorize_confirmed",)

    brbank_send_notice = fields.Selection(related="payment_mode_id.brbank_send_notice")
    brbank_can_authorize = fields.Boolean(compute="_compute_brbank_can_authorize")

    @api.depends(
        "state", "brbank_send_notice", "api_batch_ids.state", "api_line_ids.state"
    )
    def _compute_brbank_can_authorize(self):
        for order in self:
            order.brbank_can_authorize = (
                order.brbank_send_notice == "authorize_in_odoo"
                and order.state == "open"
                and bool(order._brbank_batches_to_authorize())
            )

    def _brbank_batches_to_authorize(self):
        self.ensure_one()
        return self.api_batch_ids.filtered(
            lambda batch: batch.state == "sent" and batch._brbank_lines_to_authorize()
        )

    def _brbank_check_can_authorize(self):
        if not self.env.user.has_group("account.group_account_manager"):
            raise AccessError(_("Only accounting managers authorize at the bank."))
        for order in self:
            if (
                order.brbank_send_notice != "authorize_in_odoo"
                or not order._brbank_batches_to_authorize()
            ):
                raise UserError(
                    _("Payment order %s has nothing to authorize.", order.name)
                )

    def action_brbank_authorize(self):
        self._brbank_check_can_authorize()
        return self.env["account.payment.api.second.factor"]._run_after_check(
            self, "_brbank_authorize_confirmed"
        )

    def _brbank_authorize_confirmed(self):
        """Move the money of the payments the bank validated and holds."""
        self._brbank_check_can_authorize()
        for order in self:
            for batch in order._brbank_batches_to_authorize():
                batch._brbank_authorize()
        return {"type": "ir.actions.client", "tag": "reload"}
