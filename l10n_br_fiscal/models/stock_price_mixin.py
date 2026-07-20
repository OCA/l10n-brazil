# Copyright (C) 2024 Diego Paradeda - KMEE <diego.paradeda@kmee.com.br>
# Copyright (C) 2026 KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models
from odoo.tools.float_utils import float_round

from ..constants.fiscal import TAX_FRAMEWORK_SIMPLES_ALL

# Tax domains whose input credit can be derived from the line CST plus the
# buyer company tax regime. The other domains present on the mixin (icmsst,
# issqn, irpj) have no general legal input credit, so their flags default to
# False and are manual-only.
CREDITABLE_TAX_DOMAINS = ("icms", "ipi", "pis", "cofins")


class StockPriceMixin(models.AbstractModel):
    _name = "l10n_br_fiscal.stock.price.mixin"
    _description = "Stock Price Mixin"

    freight_value_to_stock = fields.Boolean(
        string="freight_value_to_stock",
        default=True,
    )

    insurance_value_to_stock = fields.Boolean(
        string="insurance_value_to_stock",
        default=True,
    )

    other_value_to_stock = fields.Boolean(
        string="other_value_to_stock",
        default=True,
    )

    issqn_tax_is_creditable = fields.Boolean(
        string="ISSQN Creditável",
    )

    irpj_tax_is_creditable = fields.Boolean(
        string="IRPJ Creditável",
    )

    icmsst_tax_is_creditable = fields.Boolean(
        string="ICMS ST Creditável",
    )

    icms_tax_is_creditable = fields.Boolean(
        string="ICMS Creditável",
        compute="_compute_taxes_creditable",
        store=True,
        readonly=False,
    )
    ipi_tax_is_creditable = fields.Boolean(
        string="IPI Creditável",
        compute="_compute_taxes_creditable",
        store=True,
        readonly=False,
    )
    cofins_tax_is_creditable = fields.Boolean(
        string="COFINS Creditável",
        compute="_compute_taxes_creditable",
        store=True,
        readonly=False,
    )
    pis_tax_is_creditable = fields.Boolean(
        string="PIS Creditável",
        compute="_compute_taxes_creditable",
        store=True,
        readonly=False,
    )

    valuation_via_stock_price = fields.Boolean(
        compute="_compute_valuation_via_stock_price",
        store=True,
        readonly=False,
        help="Determina se o valor utilizado no custeamento automático será padrão do"
        " Odoo ou com base no campo cost_unit.\n\n"
        "    * Usar True para valor de estoque líquido (sem imposto)",
    )

    cost_unit_currency_id = fields.Many2one(
        comodel_name="res.currency",
        string="Cost Unit Currency",
        default=lambda self: self.env.ref("base.BRL"),
    )

    cost_unit = fields.Monetary(
        string="Unit Cost",
        compute="_compute_cost_unit",
        currency_field="cost_unit_currency_id",
        help="Net acquisition cost per unit: line total minus recoverable"
        " taxes (art. 301 RIR/2018, CPC 16).",
    )

    def _creditable_tax_regime_gates(self):
        """Which tax domains the BUYER company may credit, by tax regime.

        The CST states whether the operation allows a credit by nature; the
        company regime states whether this buyer may take it:
        - Simples Nacional takes no credit at all (LC 123/2006, art. 23);
        - IPI is only creditable by industries and assimilated (RIPI);
        - PIS/COFINS credits only exist in the non-cumulative regime
          (Lucro Real - Leis 10.637/2002 e 10.833/2003).
        """
        self.ensure_one()
        company = self.company_id
        simples = company.tax_framework in TAX_FRAMEWORK_SIMPLES_ALL
        industry = company.is_industry or company.ripi
        non_cumulative = company.profit_calculation == "real"
        return {
            "icms": not simples,
            "ipi": not simples and industry,
            "pis": not simples and non_cumulative,
            "cofins": not simples and non_cumulative,
        }

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
        "company_id",
    )
    def _compute_taxes_creditable(self):
        """Derive the creditable flags from the line CST + company regime.

        Computed (not onchange) so programmatic flows - purchase orders
        creating stock moves, imported fiscal documents - get the right
        creditability without any UI interaction. ``readonly=False`` keeps
        the flags editable line by line: the same product may be bought
        with different destinations, and the fiscal user has the last word.
        """
        for record in self:
            gates = record._creditable_tax_regime_gates()
            for domain in CREDITABLE_TAX_DOMAINS:
                cst = record[f"{domain}_cst_id"]
                record[f"{domain}_tax_is_creditable"] = bool(
                    gates[domain] and cst.default_creditable_tax
                )

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
    )
    def _compute_cost_unit(self):
        """Subtract creditable taxes from the unit cost."""
        for record in self:
            record.cost_unit = 0

            if not hasattr(record, "product_uom_qty"):
                continue

            if record.fiscal_operation_line_id and record.product_uom_qty:
                price = record.fiscal_amount_total

                if not record.freight_value_to_stock:
                    price -= record.freight_value
                if not record.insurance_value_to_stock:
                    price -= record.insurance_value
                if not record.other_value_to_stock:
                    price -= record.other_value

                for tax in record.fiscal_tax_ids:
                    creditable = getattr(
                        record, f"{tax.tax_domain}_tax_is_creditable", False
                    )
                    if creditable:
                        price -= getattr(record, f"{tax.tax_domain}_value", 0.0)

                # Simples Nacional supplier: the transferable CSOSN 101/201
                # credit (LC 123/2006, art. 23, §§ 1-2) reduces the buyer
                # cost - unless the buyer itself is Simples, which takes
                # no credit. It is a highlighted credit, not part of the
                # invoice total, so it is deducted here.
                if (
                    record.icmssn_credit_value
                    and record.company_id.tax_framework not in TAX_FRAMEWORK_SIMPLES_ALL
                ):
                    price -= record.icmssn_credit_value

                # ICMS relief (desoneração) is already removed from
                # fiscal_amount_total by _rm_fields_to_amount, so it must
                # not be subtracted again here.

                price_precision = self.env["decimal.precision"].precision_get(
                    "Product Price"
                )
                record.cost_unit = float_round(
                    (price / record.product_uom_qty), precision_digits=price_precision
                )
