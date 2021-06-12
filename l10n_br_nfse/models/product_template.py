# Copyright 2020 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    fiscal_deductions_value = fields.Monetary(
        string="Fiscal Deductions",
        default=0.00,
    )
