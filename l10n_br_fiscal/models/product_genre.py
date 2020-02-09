# Copyright (C) 2019 Renato Lima - Akretion <renato.lima@akretion.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models


class ProductGenre(models.Model):
    _name = "l10n_br_fiscal.product.genre"
    _inherit = "l10n_br_fiscal.data.abstract"
    _description = "Fiscal Product Genre"

    product_tmpl_ids = fields.One2many(
        comodel_name="product.template",
        string="Products",
        compute="_compute_product_tmpl_info")

    product_tmpl_qty = fields.Integer(
        string="Products Quantity",
        compute="_compute_product_tmpl_info")

    def _compute_product_tmpl_info(self):
        for record in self:
            product_tmpls = record.env["product.template"].search(
                [
                    ("fiscal_genre_id", "=", record.id),
                    "|",
                    ("active", "=", False),
                    ("active", "=", True),
                ]
            )
            record.product_tmpl_ids = product_tmpls
            record.product_tmpl_qty = len(product_tmpls)
