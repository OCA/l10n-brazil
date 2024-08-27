# @ 2019 Akretion - www.akretion.com.br -
#   Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class SaleOrderLine(models.Model):
    _name = "sale.order.line"
    _inherit = [_name, "l10n_br_fiscal.document.line.mixin"]

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

    discount = fields.Float(
        compute="_compute_discounts",
        store=True,
    )

    discount_value = fields.Monetary(
        compute="_compute_discounts",
        store=True,
    )

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

    user_total_discount = fields.Boolean(compute="_compute_user_total_discount")
    user_discount_value = fields.Boolean(compute="_compute_user_discount_value")

    cnae_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.cnae",
        string="CNAE Code",
        domain=lambda self: self._cnae_domain(),
    )

    # Depends on price_unit because we need a field to force compute in new records
    # not created yet. This field is necessary to compute readonly condition for
    # discount/discount value.
    @api.depends("price_unit")
    def _compute_user_total_discount(self):
        for rec in self:
            if self.env.user.has_group("l10n_br_sale.group_total_discount"):
                rec.user_total_discount = True
            else:
                rec.user_total_discount = False

    # Depends on price_unit because we need a field to force compute in new records
    # not created yet. This field is necessary to compute readonly condition for
    # discount/discount value.
    @api.depends("price_unit")
    def _compute_user_discount_value(self):
        for rec in self:
            if self.env.user.has_group("l10n_br_sale.group_discount_per_value"):
                rec.user_discount_value = True
            else:
                rec.user_discount_value = False

    @api.model
    def _cnae_domain(self):
        company = self.env.company
        domain = []
        if company.cnae_main_id and company.cnae_secondary_ids:
            cnae_main_id = (company.cnae_main_id.id,)
            cnae_secondary_ids = company.cnae_secondary_ids.ids
            domain = ["|", ("id", "in", cnae_secondary_ids), ("id", "=", cnae_main_id)]
        return domain

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
            line._update_fiscal_taxes()
            # Call mixin compute method
            line._compute_amounts()
            # Update record
            line.update(
                {
                    "price_tax": line.amount_tax,
                    "price_total": line.amount_total,
                }
            )
        return result

    def _prepare_invoice_line(self, **optional_values):
        self.ensure_one()
        result = {}
        if not self.display_type and self.fiscal_operation_id:
            # O caso Brasil se caracteriza por ter a Operação Fiscal
            result = self._prepare_br_fiscal_dict()
            if self.product_id and self.product_id.invoice_policy == "delivery":
                result["fiscal_quantity"] = self.qty_to_invoice
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

    def need_change_discount_value(self):
        return not self.user_discount_value or (
            self.user_total_discount and not self.discount_fixed
        )

    @api.depends(
        "order_id",
        "order_id.discount_rate",
        "discount_fixed",
        "product_uom_qty",
        "price_unit",
        "discount",
        "discount_value",
    )
    def _compute_discounts(self):
        for line in self:
            if not line.discount_fixed and line.user_total_discount:
                line.discount = line.order_id.discount_rate
            elif not line.need_change_discount_value():
                line.discount = (line.discount_value * 100) / (
                    line.product_uom_qty * line.price_unit or 1
                )
            if line.need_change_discount_value():
                line.discount_value = (line.product_uom_qty * line.price_unit) * (
                    line.discount / 100
                )

    @api.onchange("fiscal_tax_ids")
    def _onchange_fiscal_tax_ids(self):
        if self.product_id and self.fiscal_operation_line_id:
            super()._onchange_fiscal_tax_ids()
            self.tax_id = self.fiscal_tax_ids.account_taxes(
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
                self.order_id.date_order,
                "sale",
                fiscal_position=self.order_id.fiscal_position_id,
                product_price_unit=self._get_display_price(self.product_id),
                product_currency=self.order_id.currency_id,
            )
        elif self.fiscal_operation_id.default_price_unit == "cost_price":
            self.price_unit = self.product_id.standard_price
        else:
            self.price_unit = 0.00
