# Copyright 2025 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountPaymentMode(models.Model):
    _inherit = "account.payment.mode"

    generate_boletos_on_invoice = fields.Boolean(
        string="Generate boletos on invoice?",
        help=(
            "If true, when confirming the invoice with this payment method, "
            "the boletos will be automatically generated using the associated "
            "payment provider"
        ),
    )

    payment_boleto_penalty = fields.Float(
        string="Penalty",
        help=(
            "Penalty fee for overdue payments. "
            "This value will be added to the total amount of the invoice."
        ),
    )

    payment_boleto_interest = fields.Float(
        string="Interest",
        help=(
            "Interest fee for overdue payments. "
            "This value will be added to the total amount of the invoice."
        ),
    )
    payment_boleto_instructions = fields.Text(
        string="Instructions",
        help=(
            "Instructions to be printed on the boleto. "
            "This field is used to provide additional information to the payer."
        ),
    )

    payment_provider_id = fields.Many2one(
        comodel_name="payment.provider", string="Payment provider"
    )
