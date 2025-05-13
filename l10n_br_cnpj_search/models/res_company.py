# Copyright 2022 KMEE - Luis Felipe Mileo
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    equity_capital = fields.Monetary(related="partner_id.equity_capital")

    mobile = fields.Char(related="partner_id.mobile")

    company_currency_id = fields.Many2one(
        "res.currency",
        related="currency_id",
        string="Company Currency",
        readonly=True,
    )

    company_type = fields.Selection(
        related="partner_id.company_type",
    )
