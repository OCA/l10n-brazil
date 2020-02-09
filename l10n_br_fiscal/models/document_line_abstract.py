# Copyright (C) 2019  Renato Lima - Akretion <renato.lima@akretion.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models
from odoo.addons import decimal_precision as dp

from ..constants.fiscal import (CFOP_DESTINATION_EXPORT, FISCAL_IN,
                                FISCAL_OUT, NCM_FOR_SERVICE_REF,
                                PRODUCT_FISCAL_TYPE,
                                PRODUCT_FISCAL_TYPE_SERVICE,
                                TAX_DOMAIN_COFINS,
                                TAX_DOMAIN_ICMS, TAX_DOMAIN_ICMS_SN,
                                TAX_DOMAIN_IPI, TAX_DOMAIN_PIS,
                                TAX_FRAMEWORK,
                                TAX_FRAMEWORK_NORMAL,
                                TAX_FRAMEWORK_SIMPLES_ALL)


class DocumentLineAbstract(models.AbstractModel):
    _name = "l10n_br_fiscal.document.line.abstract"
    _inherit = "l10n_br_fiscal.document.line.mixin"
    _description = "Fiscal Document Line Abstract"

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
        for record in self:
            round_curr = record.document_id.currency_id.round
            record.amount_untaxed = round_curr(record.price * record.quantity)
            record.amount_tax = 0.00
            record.amount_total = (
                record.amount_untaxed +
                record.amount_tax +
                record.insurance_value +
                record.other_costs_value +
                record.freight_value -
                record.discount
            )

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

    # TODO REMOVE
    def _set_default_taxes(self, company_id, operation_type=FISCAL_OUT):
        company = self.env["res.company"].browse(company_id)
        defaults = {}
        if not self.env.context.get("default_operation_type") == FISCAL_OUT:
            return defaults

        for tax_def in company.tax_definition_ids:
            # Default ICMS SN
            if tax_def.tax_group_id.tax_domain == TAX_DOMAIN_ICMS_SN:
                if company.tax_framework in TAX_FRAMEWORK_SIMPLES_ALL:
                    defaults["icmssn_tax_id"] = tax_def.tax_id.id
                    defaults["icmssn_cst_id"] = tax_def.tax_id.cst_from_tax(
                        operation_type
                    ).id

            # Default ICMS
            if tax_def.tax_group_id.tax_domain == TAX_DOMAIN_ICMS:
                if company.tax_framework == TAX_FRAMEWORK_NORMAL:
                    defaults["icms_tax_id"] = tax_def.tax_id.id
                    defaults["icms_cst_id"] = tax_def.tax_id.cst_from_tax(
                        operation_type
                    ).id

            # Default IPI
            if tax_def.tax_group_id.tax_domain == TAX_DOMAIN_IPI:
                if company.tax_framework in TAX_FRAMEWORK_SIMPLES_ALL:
                    defaults["ipi_tax_id"] = tax_def.tax_id.id
                    defaults["ipi_cst_id"] = tax_def.tax_id.cst_from_tax(
                        operation_type
                    ).id

            if company.tax_framework == TAX_FRAMEWORK_NORMAL and not company.ripi:
                defaults["ipi_tax_id"] = tax_def.tax_id.id
                defaults["ipi_cst_id"] = tax_def.tax_id.cst_from_tax(operation_type).id

            # Default PIS/COFINS
            if tax_def.tax_group_id.tax_domain == TAX_DOMAIN_PIS:
                defaults["pis_tax_id"] = tax_def.tax_id.id
                defaults["pis_cst_id"] = tax_def.tax_id.cst_from_tax(operation_type).id

            if tax_def.tax_group_id.tax_domain == TAX_DOMAIN_COFINS:
                defaults["cofins_tax_id"] = tax_def.tax_id.id
                defaults["cofins_cst_id"] = tax_def.tax_id.cst_from_tax(
                    operation_type
                ).id

        return defaults

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
        if not self.uot_id:
            self.uot_id = self.uom_id

        if self.uom_id == self.uot_id:
            self.fiscal_price = self.price
            self.fiscal_quantity = self.quantity

        if self.uom_id != self.uot_id:
            self.fiscal_price = self.price / self.product_id.uot_factor
            self.fiscal_quantity = self.quantity * self.product_id.uot_factor

    @api.onchange("ncm_id", "nbs_id", "cest_id")
    def _onchange_ncm_id(self):
        self._onchange_operation_id()
