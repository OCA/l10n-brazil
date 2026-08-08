# Copyright 2026 - TODAY, Wesley Oliveira <wesley.oliveira@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class PurchaseBlanketOrderLine(models.Model):
    _name = "purchase.blanket.order.line"
    _inherit = [_name, "l10n_br_fiscal.document.line.mixin"]

    country_id = fields.Many2one(related="company_id.country_id", store=True)

    @api.model
    def _fiscal_operation_domain(self):
        return [("state", "=", "approved")]

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
    fiscal_tax_ids = fields.Many2many(
        comodel_name="l10n_br_fiscal.tax",
        relation="fiscal_purchase_blanket_order_line_tax_rel",
        column1="document_id",
        column2="fiscal_tax_id",
        string="Fiscal Taxes",
    )
    quantity = fields.Float(
        string="Product Uom Quantity",
        related="original_uom_qty",
    )
    uom_id = fields.Many2one(
        related="product_uom",
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
    price_gross = fields.Monetary(
        compute="_compute_amount", string="Gross Amount", compute_sudo=True
    )
    comment_ids = fields.Many2many(
        comodel_name="l10n_br_fiscal.comment",
        relation="purchase_blanket_order_line_comment_rel",
        column1="purchase_blanket_order_line_id",
        column2="comment_id",
        string="Comments",
    )
    price_subtotal = fields.Monetary(compute_sudo=True)
    price_tax = fields.Monetary(compute_sudo=True)
    price_total = fields.Monetary(compute_sudo=True)

    # adapted for _compute_find_final:
    def _get_document(self):
        self.ensure_one()
        return self.order_id

    @api.model
    def _cnae_domain(self):
        company = self.env.company
        domain = []
        if company.cnae_main_id and company.cnae_secondary_ids:
            cnae_main_id = company.cnae_main_id.id
            cnae_secondary_ids = company.cnae_secondary_ids.ids
            domain = [
                "|",
                ("id", "in", cnae_secondary_ids),
                ("id", "=", cnae_main_id),
            ]
        return domain

    cnae_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.cnae",
        string="CNAE Code",
        domain=lambda self: self._cnae_domain(),
    )

    def _setup_complete(self):
        # Same approach as l10n_br_purchase: mixin fields use precompute=True but
        # blanket lines do not have all dependencies ready at create time.
        res = super()._setup_complete()
        mixin = self.env["l10n_br_fiscal.document.line.mixin"]
        mixin_fields = mixin._fields
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

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            product_id = vals.get("product_id")
            if product_id:
                product = self.env["product.product"].browse(product_id)
                vals["product_uom"] = product.uom_po_id.id or product.uom_id.id
                vals["uom_id"] = vals["product_uom"]
                vals["uot_id"] = vals["product_uom"]
        # Like l10n_br_purchase / sale blanket: ensure taxes_id after create when
        # onchange path did not run (e.g. Command.create from parent).
        lines = super().create(vals_list)
        for line in lines.filtered("fiscal_operation_line_id"):
            line._onchange_fiscal_tax_ids()
        return lines

    def _get_protected_fields(self):
        protected_fields = super()._get_protected_fields()
        return protected_fields + [
            "fiscal_tax_ids",
            "fiscal_operation_id",
            "fiscal_operation_line_id",
        ]

    @api.depends(
        "partner_id",
        "fiscal_tax_ids",
        "product_id",
        "price_unit",
        "quantity",
        "uom_id",
        "fiscal_price",
        "fiscal_quantity",
        "uot_id",
        "discount_value",
        "insurance_value",
        "ii_customhouse_charges",
        "ii_iof_value",
        "other_value",
        "freight_value",
        "ncm_id",
        "nbs_id",
        "nbm_id",
        "cest_id",
        "fiscal_operation_line_id",
        "cfop_id",
        "icmssn_range_id",
        "icms_origin",
        "icms_cst_id",
        "ind_final",
        "icms_relief_id",
        "order_id.company_id",
        "order_id.currency_id",
    )
    def _compute_tax_fields(self):
        for line in self:
            line.company_id = line.order_id.company_id
            line.currency_id = line.order_id.currency_id
        return super()._compute_tax_fields()

    @api.onchange("product_id", "original_uom_qty")
    def onchange_product(self):
        """OCA onchange_product sets taxes_id from supplier_taxes_id (empty on BR).

        Re-sync like l10n_br_purchase after the OCA onchange.
        """
        res = super().onchange_product()
        self._onchange_fiscal_tax_ids()
        return res

    @api.onchange("fiscal_tax_ids")
    def _onchange_fiscal_tax_ids(self):
        # Same hook used by l10n_br_purchase / purchase_request / requisition.
        if self.fiscal_operation_line_id:
            self.taxes_id = self.fiscal_tax_ids.account_taxes(
                user_type="purchase",
                fiscal_operation=self.fiscal_operation_id,
                company=self.company_id or self.order_id.company_id,
            )

    @api.depends(
        "quantity",
        "price_unit",
        "fiscal_price",
        "fiscal_quantity",
        "fiscal_tax_ids",
    )
    def _compute_amount(self):
        result = super()._compute_amount()
        for line in self:
            line.update(
                {
                    "price_subtotal": line.fiscal_amount_untaxed,
                    "price_tax": line.fiscal_amount_tax,
                    "price_gross": line.fiscal_amount_untaxed,
                    "price_total": line.fiscal_amount_total,
                }
            )
        return result

    def _compute_price_unit_fiscal(self):
        for line in self:
            if line.fiscal_operation_id.default_price_unit == "cost_price":
                line.price_unit = line.product_id._get_tax_included_unit_price(
                    line.company_id,
                    line.order_id.currency_id,
                    line.order_id.date_start,
                    "purchase",
                    fiscal_position=line.order_id.fiscal_position_id,
                    product_price_unit=line.price_unit,
                    product_currency=line.order_id.currency_id,
                )
            elif line.fiscal_operation_id.default_price_unit == "sale_price":
                line.price_unit = line.product_id.lst_price
            else:
                line.price_unit = 0.00
