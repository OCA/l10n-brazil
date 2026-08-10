# Copyright 2023 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models

from odoo.addons.l10n_br_fiscal.constants.fiscal import FISCAL_TAX_ID_FIELDS


class SaleBlanketOrderLine(models.Model):
    _name = "sale.blanket.order.line"
    _inherit = [_name, "l10n_br_fiscal.document.line.mixin"]

    country_id = fields.Many2one(related="company_id.country_id", store=True)

    @api.model
    def _fiscal_operation_domain(self):
        domain = [("state", "=", "approved")]
        return domain

    fiscal_operation_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.operation",
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
    )

    fiscal_qty_delivered = fields.Float(
        string="Fiscal Utm Qty Delivered",
        related="delivered_uom_qty",
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

    comment_ids = fields.Many2many(
        comodel_name="l10n_br_fiscal.comment",
        relation="sale_blanket_order_line_comment_rel",
        column1="sale_blanket_order_line_id",
        column2="comment_id",
        string="Comments",
    )

    # Fields compute need parameter compute_sudo
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
            domain = ["|", ("id", "in", cnae_secondary_ids), ("id", "=", cnae_main_id)]
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

    def _get_protected_fields(self):
        protected_fields = super()._get_protected_fields()
        return protected_fields + [
            "fiscal_tax_ids",
            "fiscal_operation_id",
            "fiscal_operation_line_id",
        ]

    def _needs_fiscal_tax_recompute(self, vals):
        return "fiscal_tax_ids" in vals or any(
            fname in vals for fname in FISCAL_TAX_ID_FIELDS
        )

    def _recompute_fiscal_tax_fields(self):
        # _compute_tax_fields writes tax outputs; skip re-entry via write().
        self.with_context(skip_fiscal_tax_recompute=True)._compute_tax_fields()

    @api.model_create_multi
    def create(self, vals_list):
        # Like l10n_br_purchase_request: ensure taxes_id after create when
        # onchange path did not run (e.g. Command.create from parent).
        lines = super().create(vals_list)
        for line in lines.filtered("fiscal_operation_line_id"):
            line._onchange_fiscal_tax_ids()
        # Form save often creates with fiscal_tax_ids + *_tax_id together;
        # the mixin compute can run before both values settle and leave
        # amount_tax_withholding at 0. Force a final recompute.
        if any(self._needs_fiscal_tax_recompute(vals) for vals in vals_list):
            lines._recompute_fiscal_tax_fields()
        return lines

    def write(self, vals):
        res = super().write(vals)
        if self.env.context.get("skip_fiscal_tax_recompute"):
            return res
        # Same race as create: writing inss_wh_tax_id together with
        # fiscal_tax_ids can make _compute_tax_fields run on stale taxes
        # and persist amount_tax_withholding=0 after an onchange showed 11.
        if self._needs_fiscal_tax_recompute(vals):
            self._recompute_fiscal_tax_fields()
        return res

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
        # Same approach as l10n_br_purchase_blanket_order: mixin company/currency
        # must come from the parent order for account.tax mapping.
        for line in self:
            line.company_id = line.order_id.company_id
            line.currency_id = line.order_id.currency_id
        return super()._compute_tax_fields()

    @api.onchange("product_id", "original_uom_qty")
    def onchange_product(self):
        """OCA onchange_product sets taxes_id from product.taxes_id (empty on BR).

        Re-sync like l10n_br_purchase / purchase_request after the OCA onchange.
        """
        res = super().onchange_product()
        self._onchange_fiscal_tax_ids()
        return res

    @api.onchange("fiscal_tax_ids")
    def _onchange_fiscal_tax_ids(self):
        # Same hook used by l10n_br_purchase / purchase_request / requisition.
        if self.fiscal_operation_line_id:
            self.taxes_id = self.fiscal_tax_ids.account_taxes(
                user_type="sale",
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
        """Compute the amounts of the Sale Blanket Order line."""
        result = super()._compute_amount()
        for line in self:
            # Mirror l10n_br_sale: map commercial totals from fiscal amounts.
            line.update(
                {
                    "price_subtotal": line.fiscal_amount_untaxed,
                    "price_tax": line.fiscal_amount_tax,
                    "price_total": line.fiscal_amount_total,
                }
            )
        return result

    def _compute_price_unit_fiscal(self):
        for line in self:
            if (
                line.fiscal_operation_id.default_price_unit == "sale_price"
                and line.order_id.pricelist_id
                and line.order_id.partner_id
            ):
                line.price_unit = line.product_id._get_tax_included_unit_price(
                    line.company_id,
                    line.order_id.currency_id,
                    line.order_id.validity_date,
                    "sale",
                    fiscal_position=line.order_id.fiscal_position_id,
                    product_price_unit=line._get_display_price(line.product_id),
                    product_currency=line.order_id.currency_id,
                )
            elif line.fiscal_operation_id.default_price_unit == "cost_price":
                line.price_unit = line.product_id.standard_price
            else:
                line.price_unit = 0.00
