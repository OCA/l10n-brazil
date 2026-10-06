# Copyright 2020 - TODAY, Marcel Savegnago - Escodoo - https://www.escodoo.com.br
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class RepairFee(models.Model):
    _name = "repair.fee"
    _inherit = [_name, "l10n_br_repair.fiscal.line.mixin"]

    # Adapt Mixin's fields
    fiscal_tax_ids = fields.Many2many(
        comodel_name="l10n_br_fiscal.tax",
        relation="fiscal_repair_fee_tax_rel",
        column1="document_id",
        column2="fiscal_tax_id",
        string="Fiscal Taxes",
    )

    tax_framework = fields.Selection(
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
        relation="repair_fee_comment_rel",
        column1="repair_fee_id",
        column2="comment_id",
        string="Comments",
    )

    quantity = fields.Float(
        string="Part Quantity",
        related="product_uom_qty",
    )

    uom_id = fields.Many2one(
        related="product_uom",
    )

    company_id = fields.Many2one(
        related="repair_id.company_id",
        store=True,
    )

    tax_id = fields.Many2many(
        compute="_compute_tax_id",
        store=True,
        readonly=False,
        precompute=True,
    )

    @api.depends("product_id", "fiscal_tax_ids", "fiscal_operation_line_id")
    def _compute_tax_id(self):
        self._compute_l10n_br_repair_tax_id()

    @api.depends(
        "price_unit",
        "repair_id",
        "product_uom_qty",
        "product_id",
        "tax_id",
        "fiscal_amount_untaxed",
        "fiscal_amount_total",
    )
    def _compute_price_total_and_subtotal(self):
        res = super()._compute_price_total_and_subtotal()
        self._compute_l10n_br_repair_amounts()
        return res

    def _prepare_br_invoice_line(self, fiscal_position, name):
        vals = super()._prepare_br_invoice_line(fiscal_position, name)
        vals["repair_fee_ids"] = [(4, self.id)]
        return vals
