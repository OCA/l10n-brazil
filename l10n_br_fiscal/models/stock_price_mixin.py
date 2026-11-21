# Copyright (C) 2024 Diego Paradeda - KMEE <diego.paradeda@kmee.com.br>
# Copyright (C) 2026 KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.float_utils import float_round

from ..constants.fiscal import TAX_FRAMEWORK_SIMPLES_ALL
from .tax_creditability_mixin import CREDITABLE_TAX_DOMAINS

# LC 123/2006, art. 23, par. 1: the CSOSN credit is for resale and industry.
CSOSN_CREDIT_DESTINATIONS = ("purchase_industry", "purchase_commerce")

# Where the creditability of a line came from. It answers "who decided
# this", which is what makes the number auditable later.
CREDITABILITY_ORIGIN = [
    ("derived", "Derived from the tax rules"),
    ("manual", "Decided by the user"),
    ("document", "Taken from the incoming document"),
    ("undetermined", "Undetermined"),
]


class StockPriceMixin(models.AbstractModel):
    """Net acquisition cost of a line, net of recoverable taxes.

    Combine it with the fiscal line mixin (fiscal_amount_total, cfop_id,
    partner_id, company_id...) and a model whose ``quantity`` is related to
    its own quantity field.
    """

    _name = "l10n_br_fiscal.stock.price.mixin"
    _inherit = "l10n_br_fiscal.tax.creditability.mixin"
    _description = "Stock Price Mixin"

    freight_value_to_stock = fields.Boolean(
        string="Freight in Stock Value",
        default=True,
    )

    insurance_value_to_stock = fields.Boolean(
        string="Insurance in Stock Value",
        default=True,
    )

    other_value_to_stock = fields.Boolean(
        string="Other Costs in Stock Value",
        default=True,
    )

    issqn_tax_is_creditable = fields.Boolean(
        string="ISSQN Creditable",
    )

    irpj_tax_is_creditable = fields.Boolean(
        string="IRPJ Creditable",
    )

    icmsst_tax_is_creditable = fields.Boolean(
        string="ICMS ST Creditable",
    )

    icms_tax_is_creditable = fields.Boolean(
        string="ICMS Creditable",
        compute="_compute_taxes_creditable",
        store=True,
        readonly=False,
    )
    ipi_tax_is_creditable = fields.Boolean(
        string="IPI Creditable",
        compute="_compute_taxes_creditable",
        store=True,
        readonly=False,
    )
    cofins_tax_is_creditable = fields.Boolean(
        string="COFINS Creditable",
        compute="_compute_taxes_creditable",
        store=True,
        readonly=False,
    )
    pis_tax_is_creditable = fields.Boolean(
        string="PIS Creditable",
        compute="_compute_taxes_creditable",
        store=True,
        readonly=False,
    )

    creditability_origin = fields.Selection(
        selection=CREDITABILITY_ORIGIN,
        default="derived",
        required=True,
        help="Who decided the creditable taxes of this line.\n\n"
        "    * Derived: the tax rules, recomputed when the line changes.\n"
        "    * Decided by the user: kept as is, a reason is required.\n"
        "    * Taken from the incoming document.\n"
        "    * Undetermined: valued gross, which never understates inventory.",
    )

    creditability_reason_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.creditability.reason",
        ondelete="restrict",
        help="Why this line departs from the derived creditability.",
    )

    valuation_via_stock_price = fields.Boolean(
        compute="_compute_valuation_via_stock_price",
        store=True,
        readonly=False,
        help="Whether stock valuation uses the Odoo default price or the net"
        " acquisition cost held by cost_unit.\n\n"
        "    * True values incoming stock net of recoverable taxes",
    )

    cost_unit = fields.Float(
        string="Unit Cost",
        compute="_compute_cost_unit",
        store=True,
        digits="Product Price",
        help="Net acquisition cost per unit: line total minus recoverable"
        " taxes (art. 301 RIR/2018, CPC 16).",
    )

    @api.constrains("creditability_origin", "creditability_reason_id")
    def _check_creditability_reason(self):
        """A manual decision states why, and only a manual one may."""
        for record in self:
            if record.creditability_origin == "manual":
                if not record.creditability_reason_id:
                    raise ValidationError(
                        _(
                            "Deciding the creditable taxes by hand requires a"
                            " reason with its legal basis."
                        )
                    )
            elif record.creditability_reason_id:
                raise ValidationError(
                    _(
                        "A creditability reason only applies to a line decided"
                        " by the user."
                    )
                )

    @api.depends("company_id")
    def _compute_valuation_via_stock_price(self):
        for record in self:
            record.valuation_via_stock_price = getattr(
                record.company_id, "stock_valuation_via_stock_price", False
            )

    @api.depends(
        "icms_cst_id",
        "ipi_cst_id",
        "pis_cst_id",
        "cofins_cst_id",
        "icmssn_credit_value",
        "cfop_id",
        "partner_id",
        "company_id",
        "company_id.tax_framework",
        "company_id.piscofins_id",
        "company_id.profit_calculation",
        "company_id.is_industry",
        "company_id.ripi",
        "creditability_origin",
    )
    def _compute_taxes_creditable(self):
        """Derive the creditable flags from the three creditability gates.

        ``readonly=False`` keeps the flags editable line by line, and only a
        line whose origin is still ``derived`` is rewritten, so a decision
        taken by the user survives. The company fields are listed one by one
        because the regime gates read them.
        """
        for record in self:
            if record.creditability_origin != "derived":
                continue
            for domain in CREDITABLE_TAX_DOMAINS:
                creditable = record._resolve_tax_creditability(domain)
                record[f"{domain}_tax_is_creditable"] = creditable

    def _get_stock_cost_tax_map(self):
        """Which taxes of this line are a credit and which stay in the cost.

        :return: {tax_domain: 'credit' | 'cost'}; an undetermined line
            reports everything as cost, as it is valued.
        """
        self.ensure_one()
        undetermined = self.creditability_origin == "undetermined"
        return {
            domain: "cost"
            if undetermined or not self[f"{domain}_tax_is_creditable"]
            else "credit"
            for domain in CREDITABLE_TAX_DOMAINS
        }

    def _get_cost_unit_qty(self):
        """The quantity the net cost is divided by."""
        self.ensure_one()
        return self.quantity

    @api.depends(
        "fiscal_amount_total",
        "fiscal_tax_ids",
        "issqn_tax_is_creditable",
        "irpj_tax_is_creditable",
        "icmsst_tax_is_creditable",
        "icms_tax_is_creditable",
        "ipi_tax_is_creditable",
        "cofins_tax_is_creditable",
        "pis_tax_is_creditable",
        "freight_value_to_stock",
        "insurance_value_to_stock",
        "other_value_to_stock",
        "icmssn_credit_value",
        "amount_tax_withholding",
        "cfop_id",
        "quantity",
        "creditability_origin",
    )
    def _compute_cost_unit(self):
        """Subtract creditable taxes from the unit cost."""
        for record in self:
            record.cost_unit = 0
            quantity = record._get_cost_unit_qty()

            if record.fiscal_operation_line_id and quantity:
                # TODO: the import IOF (ii_iof_value) is not summed into
                # fiscal_amount_total by the line mixin, so it stays out of
                # the cost.

                # Withholdings are added back: a buyer obligation, not a
                # reduction of what the goods cost (CPC 16, item 11).
                price = record.fiscal_amount_total + record.amount_tax_withholding

                if not record.freight_value_to_stock:
                    price -= record.freight_value
                if not record.insurance_value_to_stock:
                    price -= record.insurance_value
                if not record.other_value_to_stock:
                    price -= record.other_value

                # An undetermined line is valued gross, which never understates
                # the inventory.
                if record.creditability_origin != "undetermined":
                    for tax in record.fiscal_tax_ids:
                        creditable = getattr(
                            record, f"{tax.tax_domain}_tax_is_creditable", False
                        )
                        if creditable:
                            price -= getattr(record, f"{tax.tax_domain}_value", 0.0)

                # Transferable CSOSN 101/201 credit (LC 123/2006, art. 23):
                # a highlighted credit, not part of the invoice total.
                if (
                    record.icmssn_credit_value
                    and record.creditability_origin != "undetermined"
                    and record.company_id.tax_framework not in TAX_FRAMEWORK_SIMPLES_ALL
                    and record.cfop_id.type_move in CSOSN_CREDIT_DESTINATIONS
                ):
                    price -= record.icmssn_credit_value

                # ICMS relief is already out of fiscal_amount_total.

                price_precision = self.env["decimal.precision"].precision_get(
                    "Product Price"
                )
                record.cost_unit = float_round(
                    (price / quantity), precision_digits=price_precision
                )
