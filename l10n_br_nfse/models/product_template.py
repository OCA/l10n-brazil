# Copyright 2020 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    fiscal_deductions_value = fields.Monetary(
        string='Fiscal Deductions',
        default=0.00,
    )
    city_taxation_code_id = fields.Many2many(
        string='City Taxation Code',
        comodel_name='l10n_br_fiscal.city.taxation.code'
    )
