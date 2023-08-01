# Copyright 2023 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class SaleBlanketOrderLine(models.Model):
    _name = "sale.blanket.order.line"
    _inherit = [_name, "l10n_br_fiscal.document.line.mixin"]

    country_id = fields.Many2one(related="company_id.country_id", store=True)

    @api.model
    def _default_fiscal_operation(self):
        return self.env.company.sale_fiscal_operation_id

    @api.model
    def _fiscal_operation_domain(self):
        domain = [("state", "=", "approved")]
        return domain

    fiscal_operation_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.operation",
        default=_default_fiscal_operation,
        domain=lambda self: self._fiscal_operation_domain(),
    )

    # This redundancy is necessary for the system to be able to load the report
    fiscal_operation_line_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.operation.line",
        string="Operation Line",
        domain="[('fiscal_operation_id', '=', fiscal_operation_id), "
        "('state', '=', 'approved')]",
    )

    # Adapt Mixin's fields
    fiscal_tax_ids = fields.Many2many(
        comodel_name="l10n_br_fiscal.tax",
        relation="fiscal_sale_blanket_order_line_tax_rel",
        column1="document_id",
        column2="fiscal_tax_id",
        string="Fiscal Taxes",
    )

    quantity = fields.Float(
        string="Product Uom Quantity",
        related="original_uom_qty",
        depends=["original_uom_qty"],
    )

    fiscal_qty_delivered = fields.Float(
        string="Fiscal Utm Qty Delivered",
        related="delivered_uom_qty",
        depends=["delivered_uom_qty"],
    )

    uom_id = fields.Many2one(
        related="product_uom",
        depends=["product_uom"],
    )

    tax_framework = fields.Selection(
        related="order_id.company_id.tax_framework",
        string="Tax Framework",
    )

    partner_id = fields.Many2one(
        comodel_name="res.partner",
        related="order_id.partner_id",
        string="Partner",
    )

    # Add Fields in model sale.blanket.order.line
    price_gross = fields.Monetary(
        compute="_compute_amount", string="Gross Amount", compute_sudo=True
    )

    comment_ids = fields.Many2many(
        comodel_name="l10n_br_fiscal.comment",
        relation="sale_blanket_order_line_comment_rel",
        column1="sale_blanket_order_line_id",
        column2="comment_id",
        string="Comments",
    )

    ind_final = fields.Selection(related="order_id.ind_final")

    # Fields compute need parameter compute_sudo
    price_subtotal = fields.Monetary(compute_sudo=True)
    price_tax = fields.Monetary(compute_sudo=True)
    price_total = fields.Monetary(compute_sudo=True)

    @api.model
    def _cnae_domain(self):
        company = self.env.company
        domain = []
        if company.cnae_main_id and company.cnae_secondary_ids:
            cnae_main_id = (company.cnae_main_id.id,)
            cnae_secondary_ids = company.cnae_secondary_ids.ids
            domain = ["|", ("id", "in", cnae_secondary_ids), ("id", "=", cnae_main_id)]
        return domain

    cnae_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.cnae",
        string="CNAE Code",
        domain=lambda self: self._cnae_domain(),
    )

    def _get_protected_fields(self):
        protected_fields = super()._get_protected_fields()
        return protected_fields + [
            "fiscal_tax_ids",
            "fiscal_operation_id",
            "fiscal_operation_line_id",
        ]

    @api.depends(
        "original_uom_qty",
        "price_unit",
        "fiscal_price",
        "fiscal_quantity",
        "taxes_id",
    )
    def _compute_amount(self):
        """Compute the amounts of the Sale Blanket Order line."""
        result = super()._compute_amount()
        for line in self:
            # Update taxes fields
            line._update_taxes()
            # Call mixin compute method
            line._compute_amounts()
            # Update record
            line.update(
                {
                    "price_subtotal": line.amount_untaxed,
                    "price_tax": line.amount_tax,
                    "price_gross": line.amount_untaxed,
                    "price_total": line.amount_total,
                }
            )
        return result

    @api.onchange("product_uom", "original_uom_qty")
    def _onchange_product_uom(self):
        """To call the method in the mixin to update
        the price and fiscal quantity."""
        self._onchange_commercial_quantity()

    @api.onchange("fiscal_tax_ids")
    def _onchange_fiscal_tax_ids(self):
        if self.product_id and self.fiscal_operation_line_id:
            super()._onchange_fiscal_tax_ids()
            self.taxes_id = self.fiscal_tax_ids.account_taxes(
                user_type="sale", fiscal_operation=self.fiscal_operation_id
            )

    def _get_product_price(self):
        self.ensure_one()

        if (
            self.fiscal_operation_id.default_price_unit == "sale_price"
            and self.order_id.pricelist_id
            and self.order_id.partner_id
        ):
            self.price_unit = self.product_id._get_tax_included_unit_price(
                self.company_id,
                self.order_id.currency_id,
                self.order_id.validity_date,
                "sale",
                fiscal_position=self.order_id.fiscal_position_id,
                product_price_unit=self._get_display_price(self.product_id),
                product_currency=self.order_id.currency_id,
            )
        elif self.fiscal_operation_id.default_price_unit == "cost_price":
            self.price_unit = self.product_id.standard_price
        else:
            self.price_unit = 0.00
