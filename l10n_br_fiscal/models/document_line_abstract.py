# Copyright (C) 2019  Renato Lima - Akretion <renato.lima@akretion.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models
from odoo.addons import decimal_precision as dp

from ..constants.fiscal import (
    CFOP_DESTINATION_EXPORT, FISCAL_IN,
    FISCAL_IN_OUT, FISCAL_OUT, NCM_FOR_SERVICE_REF,
    PRODUCT_FISCAL_TYPE,
    PRODUCT_FISCAL_TYPE_SERVICE, TAX_BASE_TYPE,
    TAX_BASE_TYPE_PERCENT, TAX_DOMAIN_COFINS,
    TAX_DOMAIN_ICMS, TAX_DOMAIN_ICMS_SN,
    TAX_DOMAIN_IPI, TAX_DOMAIN_PIS,
    TAX_FRAMEWORK,
    TAX_FRAMEWORK_NORMAL,
    TAX_FRAMEWORK_SIMPLES_ALL
)


class DocumentLineAbstract(models.AbstractModel):
    _name = "l10n_br_fiscal.document.line.abstract"
    _inherit = "l10n_br_fiscal.document.line.mixin"
    _description = "Fiscal Document Line Abstract"

    @api.one
    @api.depends(
        "fiscal_price",
        "discount_value",
        "insurance_value",
        "other_costs_value",
        "freight_value",
        "fiscal_quantity",
        "amount_tax_not_included",
        "uot_id",
        "product_id",
        "document_id.partner_id",
        "document_id.company_id")
    def _compute_amount(self):
        round_curr = self.document_id.currency_id.round
        self.amount_untaxed = round_curr(self.price * self.quantity)
        self.amount_tax = self.amount_tax_not_included
        self.amount_total = (
            self.amount_untaxed +
            self.amount_tax +
            self.insurance_value +
            self.other_costs_value +
            self.freight_value -
            self.discount_value)

    @api.model
    def _get_default_ncm_id(self):
        fiscal_type = self.env.context.get("default_fiscal_type")
        if fiscal_type == PRODUCT_FISCAL_TYPE_SERVICE:
            ncm_id = self.env.ref(NCM_FOR_SERVICE_REF)
            return ncm_id

    # used mostly to enable _inherits of account.invoice on fiscal_document
    # when existing invoices have no fiscal document.
    active = fields.Boolean(
        string="Active",
        default=True)

    name = fields.Text(string="Name")

    document_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.document.abstract",
        string="Document")

    company_id = fields.Many2one(
        comodel_name="res.company",
        related="document_id.company_id",
        store=True,
        string="Company")

    tax_framework = fields.Selection(
        selection=TAX_FRAMEWORK,
        related="company_id.tax_framework",
        string="Tax Framework")

    partner_id = fields.Many2one(
        comodel_name="res.partner",
        related="document_id.partner_id",
        string="Partner")

    currency_id = fields.Many2one(
        comodel_name="res.currency",
        related="company_id.currency_id",
        string="Currency")

    product_id = fields.Many2one(
        comodel_name="product.product",
        string="Product")

    uom_id = fields.Many2one(
        comodel_name="uom.uom",
        string="UOM")

    quantity = fields.Float(
        string="Quantity",
        digits=dp.get_precision("Product Unit of Measure"))

    price = fields.Float(
        string="Price Unit",
        digits=dp.get_precision("Product Price"))

    uot_id = fields.Many2one(
        comodel_name="uom.uom",
        string="Tax UoM")

    fiscal_type = fields.Selection(
        selection=PRODUCT_FISCAL_TYPE,
        string="Fiscal Type")

    fiscal_genre_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.product.genre",
        string="Fiscal Genre")

    ncm_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.ncm",
        index=True,
        default=_get_default_ncm_id,
        string="NCM")

    cest_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.cest",
        index=True,
        string="CEST",
        domain="[('ncm_ids', '=', ncm_id)]")

    nbs_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.nbs",
        index=True,
        string="NBS")

    service_type_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.service.type",
        string="Service Type",
        domain="[('internal_type', '=', 'normal')]")

    notes = fields.Text(
        string="Notes")

    # Amount Fields
    amount_estimate_tax = fields.Monetary(
        string="Amount Estimate Total",
        compute="_compute_amount",
        default=0.00)

    amount_untaxed = fields.Monetary(
        string="Amount Untaxed",
        compute="_compute_amount",
        default=0.00)

    amount_tax = fields.Monetary(
        string="Amount Tax",
        compute="_compute_amount",
        default=0.00)

    amount_total = fields.Monetary(
        string="Amount Total",
        compute="_compute_amount",
        default=0.00)

    @api.onchange("product_id")
    def _onchange_product_id(self):
        if self.product_id:
            self.name = self.product_id.display_name
            self.uom_id = self.product_id.uom_id
            self.ncm_id = self.product_id.ncm_id
            self.cest_id = self.product_id.cest_id
            self.nbs_id = self.product_id.nbs_id
            self.uot_id = self.product_id.uot_id or self.product_id.uom_id

        self._onchange_operation_id()

    @api.onchange("uot_id", "uom_id", "price", "quantity")
    def _onchange_commercial_quantity(self):
        if self.uom_id == self.uot_id:
            self.fiscal_price = self.price
            self.fiscal_quantity = self.quantity

        if self.uom_id != self.uot_id:
            self.fiscal_price = self.price / self.product_id.uot_factor
            self.fiscal_quantity = self.quantity * self.product_id.uot_factor

    @api.onchange("ncm_id", "nbs_id", "cest_id")
    def _onchange_ncm_id(self):
        self._onchange_operation_id()
