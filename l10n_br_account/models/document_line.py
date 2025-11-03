# Copyright (C) 2021 - TODAY Gabriel Cardoso de Faria - Kmee
# Copyright (C) 2023 - TODAY Raphaël Valyi - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models
from odoo.tools import float_compare


class FiscalDocumentLine(models.Model):
    _inherit = "l10n_br_fiscal.document.line"

    account_line_ids = fields.One2many(
        comodel_name="account.move.line",
        inverse_name="fiscal_document_line_id",
        string="Invoice Lines",
    )

    move_id = fields.Many2one(
        comodel_name="account.move",
        related="account_line_ids.move_id",
        store=True,
        precompute=True,
        string="Invoice",
    )

    document_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.document",
        string="Fiscal Document",
        compute="_compute_document_id",
        store=True,
        readonly=False,
        precompute=True,
        index=True,
        check_company=True,
        ondelete="cascade",
    )

    # -------------------------------------------------------------------------
    # PROXY FIELDS FOR _inherits SHADOWED NAMES
    # -------------------------------------------------------------------------
    # When using _inherits (delegation), fields with identical names on both the
    # child and delegated model may not synchronize correctly. To avoid ORM sync
    # issues, we define proxy_* fields related to the delegated document fields.
    # Then the child "original" fields point to the proxies, ensuring consistency
    # and editability.

    proxy_company_id = fields.Many2one(
        related="document_id.company_id",
        comodel_name="res.company",
        string="Company (proxy)",
        help="Technical Field.",
        readonly=False,
        store=True,
        precompute=True,
    )
    proxy_partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Partner (proxy)",
        help="Technical Field.",
    )
    proxy_product_id = fields.Many2one(
        comodel_name="product.product",
        string="Product (proxy)",
    )
    proxy_name = fields.Char(
        string="Name (proxy)",
        help="Technical Field.",
    )
    proxy_quantity = fields.Float(
        string="Quantity (proxy)",
        help="Technical Field.",
    )
    proxy_price_unit = fields.Float(
        string="Unit Price (proxy)",
        help="Technical mirror.",
    )

    # -------------------------------------------------------------------------
    # SHADOWED FIELDS SYNC
    # -------------------------------------------------------------------------

    company_id = fields.Many2one(
        related="proxy_company_id",
        comodel_name="res.company",
        string="Company",
        store=True,
        readonly=False,
        precompute=True,
    )
    product_id = fields.Many2one(
        related="proxy_product_id",
        comodel_name="product.product",
        string="Product",
        store=True,
        precompute=True,
        readonly=False,
    )
    uom_id = fields.Many2one(inverse="_inverse_uom_id")
    name = fields.Char(
        compute="_compute_name",
        store=True,
        precompute=True,
        readonly=False,
    )
    quantity = fields.Float(
        related="proxy_quantity",
        string="Quantity",
        store=True,
        precompute=True,
        readonly=False,
    )

    @api.depends("product_id", "proxy_name")
    def _compute_name(self):
        for line in self:
            line.name = line.proxy_name or line.product_id.display_name or False

    # Do not depend on `document_id.partner_id`, the inverse is taking care of that
    @api.depends("proxy_partner_id")
    def _compute_partner_id(self):
        for line in self:
            line.partner_id = line.proxy_partner_id or line.document_id.partner_id

    @api.depends("product_id", "fiscal_operation_id", "proxy_price_unit")
    def _compute_price_unit_fiscal(self):  # pylint: disable=missing-return
        lines_from_account = self._records_from_account()
        lines_from_fiscal = self - lines_from_account
        if lines_from_fiscal:
            super(FiscalDocumentLine, lines_from_fiscal)._compute_price_unit_fiscal()
        for line in lines_from_account:
            line.price_unit = line.proxy_price_unit

    def _records_from_account(self):
        account_flag = self._context.get("create_from_account")
        return self.filtered(lambda r: r.account_line_ids or account_flag)

    @api.depends("move_id.fiscal_document_id")
    def _compute_document_id(self):
        """
        Ensures that the `document_id` field is updated even when the document line is
        a new record (NewId) and has not yet been saved.
        """
        for line in self:
            is_draft = line.id != line._origin.id
            if (
                is_draft
                and line.move_id
                and line.move_id.fiscal_document_id
                and not line.document_id
            ):
                line.document_id = line.move_id.fiscal_document_id

    @api.onchange("product_id")
    def _inverse_product_id(self):
        for line in self:
            for aml in line.account_line_ids:
                if aml.product_id != line.product_id:
                    aml.product_id = line.product_id.id

    @api.onchange("name")
    def _inverse_name(self):
        for line in self:
            for aml in line.account_line_ids:
                if aml.name != line.name:
                    aml.name = line.name

    @api.onchange("quantity")
    def _inverse_quantity(self):
        for line in self:
            for aml in line.account_line_ids:
                if (
                    float_compare(
                        aml.quantity,
                        line.quantity,
                        self.env["decimal.precision"].precision_get(
                            "Product Unit of Measure"
                        ),
                    )
                    != 0
                ):
                    aml.quantity = line.quantity

    @api.onchange("price_unit")
    def _inverse_price_unit(self):
        for line in self:
            for aml in line.account_line_ids:
                if (
                    aml.currency_id.compare_amounts(aml.price_unit, line.price_unit)
                    != 0
                ):
                    aml.price_unit = line.price_unit

    @api.onchange("uom_id")
    def _inverse_uom_id(self):
        for line in self:
            for aml in line.account_line_ids:
                if aml.product_uom_id != line.uom_id:
                    aml.product_uom_id = line.uom_id

    @api.model
    def _sync_shadow_fields(self, vals):
        if "quantity" not in vals and "proxy_quantity" in vals:
            vals["quantity"] = vals["proxy_quantity"]
        if "price_unit" not in vals and "proxy_price_unit" in vals:
            vals["price_unit"] = vals["proxy_price_unit"]
        if "name" not in vals and "proxy_name" in vals:
            vals["name"] = vals["proxy_name"]
        if "product_id" not in vals and "proxy_product_id" in vals:
            vals["product_id"] = vals["proxy_product_id"]

    @api.model_create_multi
    def create(self, vals_list):
        """
        Override the create method to ensure it filters out account.move.line records
        that lack a valid document_id or fiscal_operation_line_id. Prevent the
        creation  of fiscal document lines without these mandatory fields to avoid
        system crashes due to invalid records. If the conditions are not met, return an
        empty list instead of creating any records. This supports the creation of
        account.move.line records with NULL values for fiscal_document_line_id where
        necessary.
        """
        for vals in vals_list:
            self._sync_shadow_fields(vals)

        if self._context.get("create_from_account"):
            # Filter out the dictionaries that do not meet the conditions
            filtered_vals_list = [
                vals
                for vals in vals_list
                if vals.get("document_id")
                and (
                    vals.get("fiscal_operation_id")
                    or vals.get("fiscal_operation_line_id")
                )
            ]
            # Stop execution and return empty if no dictionary meets the conditions
            if not filtered_vals_list:
                return []
            # Assign the filtered list back to the original list for further processing
            vals_list = filtered_vals_list

        return super().create(vals_list)

    def _update_cache(self, values, validate=True):
        """
        Overriden to avoid raising error with ensure_one() in super()
        when called from some account.move.line onchange
        as we allow empty fiscal document line in account.move.line.
        """
        if len(self) == 0:
            return
        return super()._update_cache(values, validate)
