# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    dda_auto_link = fields.Boolean(
        string="DDA automatic link",
        help="Link a boleto to its payable line by itself only when the strict "
        "rule is met: same full CNPJ, exact amount, same due date, same document "
        "number when both sides have one, and a single candidate.",
        default=False,
    )
    dda_date_tolerance = fields.Integer(
        string="DDA due date tolerance (days)",
        default=3,
        help="Difference in days between the boleto and the title still accepted "
        "as a suggestion.",
    )
    dda_amount_tolerance = fields.Monetary(
        string="DDA amount tolerance",
        currency_field="currency_id",
        default=0.0,
        help="Difference between the boleto and the title still accepted as a "
        "suggestion (never as an automatic link).",
    )
    dda_create_bill_mode = fields.Selection(
        selection=[("never", "Never"), ("draft", "Draft bill")],
        string="DDA bill creation",
        default="never",
        required=True,
        help="Whether the recommended action for a boleto without a title is to "
        "create a vendor bill in draft.",
    )
    dda_interest_account_id = fields.Many2one(
        comodel_name="account.account",
        string="DDA interest account",
        domain="[('company_id', '=', id)]",
        check_company=True,
    )
    dda_fine_account_id = fields.Many2one(
        comodel_name="account.account",
        string="DDA fine account",
        domain="[('company_id', '=', id)]",
        check_company=True,
    )
    dda_discount_account_id = fields.Many2one(
        comodel_name="account.account",
        string="DDA discount account",
        domain="[('company_id', '=', id)]",
        check_company=True,
    )
    dda_payment_mode_id = fields.Many2one(
        comodel_name="account.payment.mode",
        string="DDA payment mode",
        domain="[('payment_type', '=', 'outbound'), " "('company_id', '=', id)]",
        check_company=True,
        help="Payment mode (CNAB) of the payment order that receives the boletos.",
    )
