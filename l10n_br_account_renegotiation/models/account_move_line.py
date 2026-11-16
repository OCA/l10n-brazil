# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    installment_original_amount = fields.Monetary(
        currency_field="currency_id",
        readonly=True,
        copy=False,
        help="Amount of this installment before a renegotiation replaced it. The "
        "installment is zeroed instead of deleted, so its boleto, CNAB remittance "
        "and payment history keep pointing to it.",
    )
