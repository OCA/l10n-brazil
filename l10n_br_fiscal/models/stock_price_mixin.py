# Copyright (C) 2024 Diego Paradeda - KMEE <diego.paradeda@kmee.com.br>
# Copyright (C) 2026 KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models
from odoo.tools.float_utils import float_round

from ..constants.fiscal import TAX_FRAMEWORK_SIMPLES_ALL

# icmsst, issqn and irpj have no general input credit: their flags are manual.
CREDITABLE_TAX_DOMAINS = ("icms", "ipi", "pis", "cofins")

RESTRICTED_DESTINATIONS = ("purchase_ownuse", "purchase_asset")

# LC 123/2006, art. 23, par. 1: the CSOSN credit is for resale and industry.
CSOSN_CREDIT_DESTINATIONS = ("purchase_industry", "purchase_commerce")


class StockPriceMixin(models.AbstractModel):
    """Net acquisition cost of a line, net of recoverable taxes.

    Combine it with the fiscal line mixin (fiscal_amount_total, cfop_id,
    partner_id, company_id...) and a model whose ``quantity`` is related to
    its own quantity field.
    """

    _name = "l10n_br_fiscal.stock.price.mixin"
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

    def _is_non_cumulative(self):
        """Whether the company is under the non-cumulative PIS/COFINS regime.

        Lucro Real companies listed in art. 10 of Lei 10.833/2003 stay
        cumulative, so the company PIS/COFINS regime wins over
        ``profit_calculation``, which is only the fallback when unset.
        """
        self.ensure_one()
        regime = self.company_id.piscofins_id
        if not regime:
            return self.company_id.profit_calculation == "real"
        non_cumulative = self.env.ref(
            "l10n_br_fiscal.tax_pis_cofins_nao_columativo", raise_if_not_found=False
        )
        return bool(non_cumulative) and regime == non_cumulative

    def _creditable_tax_regime_gates(self):
        """Which tax domains the BUYER company may credit, by tax regime.

        - Simples Nacional takes no credit at all (LC 123/2006, art. 23);
        - IPI is only creditable by industries and assimilated (RIPI,
          arts. 226 and 251);
        - PIS/COFINS credits only exist in the non-cumulative regime
          (Leis 10.637/2002 e 10.833/2003, art. 3 of both).
        """
        self.ensure_one()
        company = self.company_id
        simples = company.tax_framework in TAX_FRAMEWORK_SIMPLES_ALL
        industry = company.is_industry or company.ripi
        non_cumulative = self._is_non_cumulative()
        return {
            "icms": not simples,
            "ipi": not simples and industry,
            "pis": not simples and non_cumulative,
            "cofins": not simples and non_cumulative,
        }

    def _creditable_tax_destination_gates(self):
        """Which tax domains the DESTINATION of the goods forbids.

        A veto, never a permission: it only closes domains for the
        destinations the law restricts.

        - own use and consumption: no ICMS credit until 2033 (LC 87/96,
          art. 33, I, as amended by LC 171/2019), no IPI (RIPI, art. 226)
          and no PIS/COFINS, since it is not an input (PN COSIT/RFB 5/2018);
        - fixed assets: no IPI. ICMS (CIAP) and PIS/COFINS (Lei 10.833/2003,
          art. 3, par. 14) are credited over 48 months, which is not
          implemented, so the tax stays in the cost of the asset.
        """
        self.ensure_one()
        if self.cfop_id.type_move in RESTRICTED_DESTINATIONS:
            return dict.fromkeys(CREDITABLE_TAX_DOMAINS, False)
        return {}

    def _is_simples_supplier_without_credit(self):
        """Simples supplier that transferred no ICMS credit on the document.

        A Simples Nacional supplier only transfers the credit stated under
        CSOSN 101/201 (LC 123/2006, art. 23, par. 1 and 2), which arrives in
        ``icmssn_credit_value``. PIS and COFINS do not depend on the supplier
        regime (ADI SRF 15/2007).
        """
        self.ensure_one()
        partner = self.partner_id
        if not partner or partner.tax_framework not in TAX_FRAMEWORK_SIMPLES_ALL:
            return False
        return not self.icmssn_credit_value

    def _resolve_tax_creditability(self, tax_domain):
        """Whether this line may credit ``tax_domain``.

        All three gates must allow it: the BUYER regime, the DESTINATION
        of the goods (CFOP) and the NATURE of the operation (line CST).
        """
        self.ensure_one()
        if tax_domain not in CREDITABLE_TAX_DOMAINS:
            return False

        if not self._creditable_tax_regime_gates().get(tax_domain):
            return False

        destination = self._creditable_tax_destination_gates()
        if tax_domain in destination and not destination[tax_domain]:
            return False

        if tax_domain == "icms" and self._is_simples_supplier_without_credit():
            return False

        return bool(self[f"{tax_domain}_cst_id"].default_creditable_tax)

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
    )
    def _compute_taxes_creditable(self):
        """Derive the creditable flags from the three creditability gates.

        ``readonly=False`` keeps the flags editable line by line. The company
        fields are listed one by one because the regime gates read them.
        """
        for record in self:
            for domain in CREDITABLE_TAX_DOMAINS:
                creditable = record._resolve_tax_creditability(domain)
                record[f"{domain}_tax_is_creditable"] = creditable

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
