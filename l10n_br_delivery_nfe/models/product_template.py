# Copyright (C) 2024 Diego Paradeda - KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    product_volume_type = fields.Char(
        string="Volume Type",
        help="Type of transported volumes: Mapped onto 'nfe40_esp'",
        compute="_compute_product_volume_type",
        inverse="_inverse_product_volume_type",
        store=True,
    )

    @api.depends("product_variant_ids", "product_variant_ids.product_volume_type")
    def _compute_product_volume_type(self):
        unique_variants = self.filtered(
            lambda template: len(template.product_variant_ids) == 1
        )
        for template in unique_variants:
            template.product_volume_type = (
                template.product_variant_ids.product_volume_type
            )
        for template in self - unique_variants:
            template.product_volume_type = ""

    def _inverse_product_volume_type(self):
        for template in self:
            if len(template.product_variant_ids) == 1:
                template.product_variant_ids.product_volume_type = (
                    template.product_volume_type
                )
