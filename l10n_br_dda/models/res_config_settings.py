# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    dda_auto_link = fields.Boolean(related="company_id.dda_auto_link", readonly=False)
    dda_date_tolerance = fields.Integer(
        related="company_id.dda_date_tolerance", readonly=False
    )
    dda_amount_tolerance = fields.Monetary(
        related="company_id.dda_amount_tolerance",
        currency_field="currency_id",
        readonly=False,
    )
    dda_create_bill_mode = fields.Selection(
        related="company_id.dda_create_bill_mode", readonly=False
    )
    dda_interest_account_id = fields.Many2one(
        related="company_id.dda_interest_account_id", readonly=False, check_company=True
    )
    dda_fine_account_id = fields.Many2one(
        related="company_id.dda_fine_account_id", readonly=False, check_company=True
    )
    dda_discount_account_id = fields.Many2one(
        related="company_id.dda_discount_account_id", readonly=False, check_company=True
    )
    dda_payment_mode_id = fields.Many2one(
        related="company_id.dda_payment_mode_id", readonly=False, check_company=True
    )
