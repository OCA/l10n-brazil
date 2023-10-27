# © 2016 KMEE INFORMATICA LTDA (https://kmee.com.br)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    pos_fiscal_map_ids = fields.One2many(
        comodel_name="l10n_br_pos.product_fiscal_map",
        inverse_name="product_tmpl_id",
    )

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

    @api.model_create_multi
    def create(self, vals_list):
        templates = super().create(vals_list)
        for template in templates:
            if template.available_in_pos:
                template.update_pos_fiscal_map()
        return templates

    def write(self, vals):
        if vals.get("available_in_pos"):
            self.update_pos_fiscal_map()
        return super().write(vals)
