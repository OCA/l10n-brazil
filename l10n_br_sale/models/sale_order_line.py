# @ 2019 Akretion - www.akretion.com.br -
#   Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class SaleOrderLine(models.Model):
    _name = "sale.order.line"
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
        relation="fiscal_sale_line_tax_rel",
        column1="document_id",
        column2="fiscal_tax_id",
        string="Fiscal Taxes",
    )

    quantity = fields.Float(
        string="Product Uom Quantity",
        related="product_uom_qty",
        depends=["product_uom_qty"],
    )

    fiscal_qty_delivered = fields.Float(
        string="Fiscal Utm Qty Delivered",
        compute="_compute_qty_delivered",
        compute_sudo=True,
        store=True,
        digits="Product Unit of Measure",
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

    # Add Fields in model sale.order.line
    price_gross = fields.Monetary(
        compute="_compute_amount", string="Gross Amount", compute_sudo=True
    )

    comment_ids = fields.Many2many(
        comodel_name="l10n_br_fiscal.comment",
        relation="sale_order_line_comment_rel",
        column1="sale_line_id",
        column2="comment_id",
        string="Comments",
    )

    discount_fixed = fields.Boolean(string="Fixed Discount?")

    ind_final = fields.Selection(related="order_id.ind_final")

    # Usado para tornar Somente Leitura os campos dos custos
    # de entrega quando a definição for por Total
    delivery_costs = fields.Selection(
        related="company_id.delivery_costs",
    )
    force_compute_delivery_costs_by_total = fields.Boolean(
        related="order_id.force_compute_delivery_costs_by_total"
    )

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
        "product_uom_qty",
        "price_unit",
        "discount",
        "fiscal_price",
        "fiscal_quantity",
        "discount_value",
        "freight_value",
        "insurance_value",
        "other_value",
        "tax_id",
    )
    def _compute_amount(self):
        """Compute the amounts of the SO line."""
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
                    "price_gross": line.amount_untaxed + line.discount_value,
                    "price_total": line.amount_total,
                }
            )
        return result

    def _prepare_invoice_line(self, **optional_values):
        self.ensure_one()
        result = self._prepare_br_fiscal_dict()
        if self.product_id and self.product_id.invoice_policy == "delivery":
            self._compute_qty_delivered()
            result["fiscal_quantity"] = self.fiscal_qty_delivered
        result.update(super()._prepare_invoice_line(**optional_values))
        return result

    @api.onchange("product_uom", "product_uom_qty")
    def _onchange_product_uom(self):
        """To call the method in the mixin to update
        the price and fiscal quantity."""
        self._onchange_commercial_quantity()

    @api.depends(
        "qty_delivered_method",
        "qty_delivered_manual",
        "analytic_line_ids.so_line",
        "analytic_line_ids.unit_amount",
        "analytic_line_ids.product_uom_id",
    )
    def _compute_qty_delivered(self):
        result = super()._compute_qty_delivered()
        for line in self:
            line.fiscal_qty_delivered = 0.0
            if line.product_id.invoice_policy == "delivery":
                if line.uom_id == line.uot_id:
                    line.fiscal_qty_delivered = line.qty_delivered

            if line.uom_id != line.uot_id:
                line.fiscal_qty_delivered = (
                    line.qty_delivered * line.product_id.uot_factor
                )
        return result

    @api.onchange("discount")
    def _onchange_discount_percent(self):
        """Update discount value"""
        if not self.env.user.has_group("l10n_br_sale.group_discount_per_value"):
            self.discount_value = (self.product_uom_qty * self.price_unit) * (
                self.discount / 100
            )

    @api.onchange("discount_value")
    def _onchange_discount_value(self):
        """Update discount percent"""
        if self.env.user.has_group("l10n_br_sale.group_discount_per_value"):
            self.discount = (self.discount_value * 100) / (
                self.product_uom_qty * self.price_unit or 1
            )

    @api.onchange("fiscal_tax_ids")
    def _onchange_fiscal_tax_ids(self):
        result = super()._onchange_fiscal_tax_ids()
        self.tax_id |= self.fiscal_tax_ids.account_taxes(user_type="sale")
        if self.order_id.fiscal_operation_id.deductible_taxes:
            self.tax_id |= self.fiscal_tax_ids.account_taxes(
                user_type="sale", deductible=True
            )
        return result
