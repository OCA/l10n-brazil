# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class SaleSubscriptionLine(models.Model):
    _name = "sale.subscription.line"
    _inherit = [_name, "l10n_br_fiscal.document.line.mixin"]

    @api.model
    def _fiscal_operation_domain(self):
        return [
            ("fiscal_operation_type", "=", "out"),
            ("state", "=", "approved"),
            ("fiscal_type", "not ilike", "%refund%"),
        ]

    fiscal_operation_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.operation",
        domain=lambda self: self._fiscal_operation_domain(),
    )

    fiscal_operation_line_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.operation.line",
        string="Operation Line",
        domain="[('fiscal_operation_id', '=', fiscal_operation_id), "
        "('state', '=', 'approved')]",
    )

    # Adapt Mixin's fields
    fiscal_tax_ids = fields.Many2many(
        comodel_name="l10n_br_fiscal.tax",
        relation="fiscal_sale_subscription_line_tax_rel",
        column1="document_id",
        column2="fiscal_tax_id",
        string="Fiscal Taxes",
    )

    comment_ids = fields.Many2many(
        comodel_name="l10n_br_fiscal.comment",
        relation="sale_subscription_line_comment_rel",
        column1="subscription_line_id",
        column2="comment_id",
        string="Comments",
    )

    quantity = fields.Float(
        string="Product Uom Quantity",
        related="product_uom_qty",
    )

    uom_id = fields.Many2one(
        related="product_id.uom_id",
    )

    partner_id = fields.Many2one(
        comodel_name="res.partner",
        related="sale_subscription_id.partner_id",
        string="Partner",
    )

    tax_framework = fields.Selection(
        related="sale_subscription_id.company_id.tax_framework",
        string="Tax Framework",
    )

    discount_value = fields.Monetary(
        compute="_compute_discount_value",
        store=True,
    )

    @api.model_create_multi
    def create(self, vals_list):
        # The form fills the fiscal operation of a line from its context. Lines
        # created by code (crons, imports, APIs, other modules) inherit the one
        # of the subscription, otherwise they would have no operation line, no
        # fiscal taxes and the invoice would come out with a zero total.
        for vals in vals_list:
            if "fiscal_operation_id" in vals or not vals.get("sale_subscription_id"):
                continue
            subscription = self.env["sale.subscription"].browse(
                vals["sale_subscription_id"]
            )
            if subscription.fiscal_operation_id:
                vals["fiscal_operation_id"] = subscription.fiscal_operation_id.id
        return super().create(vals_list)

    def _get_document(self):
        self.ensure_one()
        return self.sale_subscription_id

    def _setup_complete(self):
        # Same approach as l10n_br_contract: the mixin fields use precompute=True
        # but they depend on price_unit, which subscription_oca does not precompute.
        res = super()._setup_complete()
        mixin_fields = self.env["l10n_br_fiscal.document.line.mixin"]._fields
        for name, field in self._fields.items():
            mixin_field = mixin_fields.get(name)
            if not mixin_field:
                continue
            if mixin_field.compute in (
                "_compute_price_unit_fiscal",
                "_compute_product_fiscal_fields",
                "_compute_fiscal_quantity",
                "_compute_fiscal_price",
                "_compute_fiscal_tax_ids",
                "_compute_tax_fields",
                "_compute_fiscal_operation_line_id",
                "_compute_comment_ids",
            ) and getattr(mixin_field, "precompute", False):
                field.precompute = False
        return res

    @api.depends("product_uom_qty", "price_unit", "discount")
    def _compute_discount_value(self):
        for line in self:
            line.discount_value = (
                line.product_uom_qty * line.price_unit * line.discount / 100
            )

    @api.depends("fiscal_tax_ids", "fiscal_operation_id", "fiscal_operation_line_id")
    def _compute_tax_ids(self):
        fiscal_lines = self.filtered("fiscal_operation_line_id")
        for line in fiscal_lines:
            line.tax_ids = line.fiscal_tax_ids.account_taxes(
                user_type="sale",
                fiscal_operation=line.fiscal_operation_id,
                company=line.company_id,
            )
        return super(SaleSubscriptionLine, self - fiscal_lines)._compute_tax_ids()

    @api.depends("fiscal_amount_untaxed", "fiscal_amount_total")
    def _compute_subtotal(self):
        result = super()._compute_subtotal()
        for line in self.filtered("fiscal_operation_id"):
            line.update(
                {
                    "price_subtotal": line.fiscal_amount_untaxed,
                    "price_total": line.fiscal_amount_total,
                    "amount_tax_line_amount": line.fiscal_amount_total
                    - line.fiscal_amount_untaxed,
                }
            )
        return result

    def _prepare_account_move_line(self):
        values = super()._prepare_account_move_line()
        if self.fiscal_operation_id:
            values = {**self._prepare_br_fiscal_dict(), **values}
        return values

    def _prepare_sale_order_line(self):
        values = super()._prepare_sale_order_line()
        values.update(
            {
                "fiscal_operation_id": self.fiscal_operation_id.id,
                "fiscal_operation_line_id": self.fiscal_operation_line_id.id,
            }
        )
        return values
