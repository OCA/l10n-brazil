# Copyright (C) 2023 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class PosPaymentMethod(models.Model):
    _inherit = "pos.payment.method"

    payment_mode_id = fields.Many2one(
        comodel_name="account.payment.mode",
        required=False,
        string="NFe Account Payment Mode",
    )
