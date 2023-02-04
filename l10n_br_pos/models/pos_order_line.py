# © 2016 KMEE INFORMATICA LTDA (https://kmee.com.br)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class PosOrderLine(models.Model):
    _name = "pos.order.line"
    _inherit = [_name, "l10n_br_fiscal.document.line.mixin"]

    fiscal_tax_ids = fields.Many2many(
        comodel_name="l10n_br_fiscal.tax",
        relation="pos_order_line_tax_rel",
        column1="pos_order_line_id",
        column2="order_line_id",
        string="Fiscal Taxes",
    )

    comment_ids = fields.Many2many(
        comodel_name="l10n_br_fiscal.comment",
        relation="pos_order_line_fiscal_comment_rel",
        column1="pos_order_line_id",
        column2="comment_id",
        string="Comments",
    )

    quantity = fields.Float(
        string="Product Uom Quantity",
        related="qty",
        depends=["qty"],
    )

    uom_id = fields.Many2one(
        related="product_uom_id",
        depends=["product_uom_id"],
    )
