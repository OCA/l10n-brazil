# Copyright 2020 - TODAY, Marcel Savegnago - Escodoo - https://www.escodoo.com.br
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models

from ...l10n_br_fiscal.constants.fiscal import TAX_FRAMEWORK


class RepairLine(models.Model):
    _name = "repair.line"
    _inherit = [_name, "l10n_br_repair.fiscal.line.mixin"]

    # Adapt Mixin's fields
    fiscal_tax_ids = fields.Many2many(
        comodel_name="l10n_br_fiscal.tax",
        relation="fiscal_repair_line_tax_rel",
        column1="document_id",
        column2="fiscal_tax_id",
        string="Fiscal Taxes",
    )

    tax_framework = fields.Selection(
        selection=TAX_FRAMEWORK,
        related="repair_id.company_id.tax_framework",
        string="Tax Framework",
    )

    partner_id = fields.Many2one(
        comodel_name="res.partner",
        related="repair_id.partner_id",
        string="Partner",
    )

    comment_ids = fields.Many2many(
        comodel_name="l10n_br_fiscal.comment",
        relation="repair_line_comment_rel",
        column1="repair_line_id",
        column2="comment_id",
        string="Comments",
    )

    quantity = fields.Float(
        "Part Quantity",
        related="product_uom_qty",
        depends=["product_uom_qty"],
    )

    uom_id = fields.Many2one(
        related="product_uom",
        depends=["product_uom"],
    )

    company_id = fields.Many2one(
        related="repair_id.company_id",
        store=True,
    )

    @api.depends(
        "price_unit",
        "repair_id",
        "product_uom_qty",
        "product_id",
        "repair_id.invoice_method",
    )
    def _compute_price_subtotal(self):
        super()._compute_price_subtotal()
        for line in self:
            # Update taxes fields
            line._update_taxes()
            # Call mixin compute method
            line._compute_amounts()
            # Update record
            line.update(
                {
                    "price_subtotal": line.amount_untaxed,
                    # 'price_tax': line.amount_tax,
                    "price_gross": line.amount_untaxed + line.discount_value,
                    "price_total": line.amount_total,
                }
            )

    @api.onchange("product_uom", "product_uom_qty")
    def _onchange_product_uom(self):
        """To call the method in the mixin to update
        the price and fiscal quantity."""
        self._onchange_commercial_quantity()
