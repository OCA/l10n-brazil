# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountPaymentMode(models.Model):
    """The payment mode reaches the bank through `payment_provider_id` of
    the base, the single link; this module only shows what the bank does."""

    _inherit = "account.payment.mode"

    payment_provider_code = fields.Selection(related="payment_provider_id.code")
    brbank_capabilities = fields.Char(related="payment_provider_id.brbank_capabilities")
    brbank_sandbox_validated = fields.Boolean(
        related="payment_provider_id.brbank_sandbox_validated"
    )
