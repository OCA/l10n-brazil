# Copyright 2022 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models


class ProductProduct(models.Model):
    _inherit = "product.product"

    @api.depends_context("company")
    def update_pos_fiscal_map(self):
        for record in self:
            pos_config_ids = record.env["pos.config"].search(
                [("company_id", "=", self.env.company.id)]
            )
            with_maps_pos_config_id = record.pos_fiscal_map_ids.mapped("pos_config_id")
            to_create_ids = pos_config_ids - with_maps_pos_config_id

            for pos_config_id in to_create_ids:
                if not pos_config_id.partner_id:
                    continue

                pos_fiscal_map_id = record.pos_fiscal_map_ids.create(
                    {
                        "pos_config_id": pos_config_id.id,
                        "product_tmpl_id": record.id,
                        "partner_id": pos_config_id.partner_id.id,
                        "company_id": self.env.company.id,
                    }
                )

                pos_fiscal_map_id._onchange_product_id_fiscal()
                pos_fiscal_map_id._onchange_fiscal_operation_id()
                pos_fiscal_map_id._onchange_fiscal_operation_line_id()
                pos_fiscal_map_id._onchange_fiscal_taxes()
