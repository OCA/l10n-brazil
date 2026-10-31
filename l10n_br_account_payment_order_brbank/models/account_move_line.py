# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from brbank.pagamento import CapacidadePagamento

from odoo import api, models
from odoo.osv import expression


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    def _is_payment_schedule_instrument_missing(self):
        mode = self.payment_mode_id
        if (
            self.payment_pix_copy_paste
            and self.payment_pix_check != "mismatch"
            and mode.payment_order_ok
            and mode.payment_mode_domain == "pix_transfer"
            and CapacidadePagamento.PIX_QRCODE in mode._brbank_capabilities()
        ):
            return False
        return super()._is_payment_schedule_instrument_missing()

    @api.model
    def _get_payment_schedule_missing_instrument_domain(self):
        missing = super()._get_payment_schedule_missing_instrument_domain()
        modes = (
            self.env["account.payment.mode"]
            .sudo()
            .search(
                [
                    ("api_provider", "=", "brbank"),
                    ("payment_order_ok", "=", True),
                    ("payment_mode_domain", "=", "pix_transfer"),
                ]
            )
            .filtered(
                lambda mode: CapacidadePagamento.PIX_QRCODE
                in mode._brbank_capabilities()
            )
        )
        if not modes:
            return missing
        return expression.AND(
            [
                missing,
                [
                    "!",
                    "&",
                    "&",
                    ("payment_mode_id", "in", modes.ids),
                    ("payment_pix_copy_paste", "!=", False),
                    ("payment_pix_check", "!=", "mismatch"),
                ],
            ]
        )

    def _prepare_payment_line_vals(self, payment_order):
        vals = super()._prepare_payment_line_vals(payment_order)
        if self.payment_pix_copy_paste:
            vals["pix_copy_paste"] = self.payment_pix_copy_paste
        return vals
