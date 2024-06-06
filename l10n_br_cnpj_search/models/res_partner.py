# Copyright 2022 KMEE - Luis Felipe Mileo
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    equity_capital = fields.Monetary(currency_field="company_currency_id")

    cnae_secondary_ids = fields.Many2many(
        comodel_name="l10n_br_fiscal.cnae",
        relation="res_partner_fiscal_cnae_rel",
        column1="company_id",
        column2="cnae_id",
        domain="[('internal_type', '=', 'normal'), ('id', '!=', cnae_main_id)]",
        string="Secondary CNAE",
    )

    legal_nature = fields.Char()

    company_currency_id = fields.Many2one(
        comodel_name="res.currency",
        related="company_id.currency_id",
        string="Company Currency",
        readonly=True,
    )
