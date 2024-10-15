# Copyright (C) 2024 Diego Paradeda - KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models


class ProductProduct(models.Model):
    _inherit = "product.product"

    product_volume_type = fields.Char(
        string="Volume Type",
        help="Type of transported volumes: Mapped onto 'nfe40_esp'",
    )
