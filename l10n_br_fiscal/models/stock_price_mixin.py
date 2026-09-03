# Copyright (C) 2024 Diego Paradeda - KMEE <diego.paradeda@kmee.com.br>
# Copyright (C) 2026 KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.float_utils import float_round

from ..constants.fiscal import TAX_FRAMEWORK_SIMPLES_ALL

# Tax domains whose input credit can be derived from the line CST plus the
# buyer company tax regime. The other domains present on the mixin (icmsst,
# issqn, irpj) have no general legal input credit, so their flags default to
# False and are manual-only.
CREDITABLE_TAX_DOMAINS = ("icms", "ipi", "pis", "cofins")

# CFOP destinations that take no input credit at all on the acquisition.
# Own use and consumption is barred from the ICMS credit until 2033 (LC 87/96,
# art. 33, I) and is not an input for PIS/COFINS. Fixed assets do recover ICMS
# and PIS/COFINS, but only spread over 48 months (CIAP and Lei 10.833/2003,
# art. 3, par. 14); neither deferral is implemented here, so the tax stays in
# the cost of the asset instead of being written off as an immediate credit.
RESTRICTED_DESTINATIONS = ("purchase_ownuse", "purchase_asset")

# Destinations that the transferable CSOSN credit reaches: LC 123/2006,
# art. 23, par. 1 grants it for resale and manufacturing only.
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

    creditability_origin = fields.Selection(
        selection=CREDITABILITY_ORIGIN,
        default="derived",
        required=True,
        help="Who decided the creditable taxes of this line.\n\n"
        "    * Derived: the tax rules decided, and they keep deciding when"
        " the line changes.\n"
        "    * Decided by the user: the rules no longer overwrite the flags,"
        " and a reason with a legal basis is required.\n"
        "    * Taken from the incoming document: the document itself stated"
        " the credit.\n"
        "    * Undetermined: there was not enough information to decide, so"
        " the goods are valued gross, which never understates inventory.",
    )

    creditability_reason_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.creditability.reason",
        ondelete="restrict",
        help="Why this line departs from the derived creditability. The user"
        " never types a cost: picking the reason is what the law allows, and"
        " the system recomputes from it.",
    )

    valuation_via_stock_price = fields.Boolean(
        compute="_compute_valuation_via_stock_price",
        store=True,
        readonly=False,
        help="Whether stock valuation uses the Odoo default price or the net"
        " acquisition cost held by cost_unit.\n\n"
        "    * True values incoming stock net of recoverable taxes",
    )

    cost_unit_currency_id = fields.Many2one(
        comodel_name="res.currency",
        string="Cost Unit Currency",
        default=lambda self: self.env.ref("base.BRL"),
    )

    cost_unit = fields.Monetary(
        string="Unit Cost",
        compute="_compute_cost_unit",
        store=True,
        currency_field="cost_unit_currency_id",
        help="Net acquisition cost per unit: line total minus recoverable"
        " taxes (art. 301 RIR/2018, CPC 16).",
    )

    @api.constrains("creditability_origin", "creditability_reason_id")
    def _check_creditability_reason(self):
        """A manual decision states why, and only a manual one may.

        This is the line between versatility and a spreadsheet: the law does
        allow a company to depart from the general rule, but always for a
        stated reason (a conditioned benefit, a court decision, a special
        regime). A cost that cannot be rebuilt from the invoice plus the
        configuration cannot be defended, so the freedom lives in the
        justification, never in the arithmetic.
        """
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

    def _is_non_cumulative(self):
        """Whether the company is under the non-cumulative PIS/COFINS regime.

        Read from the company PIS/COFINS regime rather than from
        ``profit_calculation``: a Lucro Real company whose revenue is listed
        in art. 10 of Lei 10.833/2003 (telecom, collective transport,
        hospitals and others) stays cumulative and takes no credit. Falls
        back to the profit calculation when the regime was never set, so an
        unconfigured database keeps the previous behavior.
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

        This gate is a veto, never a permission: it closes a domain when the
        CFOP states a destination the law restricts, and stays silent when
        the destination says nothing about credit. That is what lets an
        interstate transfer between branches (CFOP 1151, 1152) keep its
        credit while a purchase for own use loses it.

        - own use and consumption: no ICMS credit until 2033 (LC 87/96,
          art. 33, I, as amended by LC 171/2019), no IPI credit (RIPI,
          art. 226) and no PIS/COFINS credit, since it is not an input
          (Parecer Normativo COSIT/RFB 5/2018);
        - fixed assets: no IPI credit (RIPI art. 226 lists no such credit).
          ICMS is creditable over 48 months through CIAP and PIS/COFINS over
          48 months as well (Lei 10.833/2003, art. 3, par. 14), but neither
          deferral is implemented here, so both stay in the cost of the
          asset. That is the conservative side: the alternative would remove
          from the asset a credit the company cannot take yet.
        """
        self.ensure_one()
        if self.cfop_id.type_move in RESTRICTED_DESTINATIONS:
            return dict.fromkeys(CREDITABLE_TAX_DOMAINS, False)
        return {}

    def _is_simples_supplier_without_credit(self):
        """Simples supplier that transferred no ICMS credit on the document.

        A Simples Nacional supplier does not highlight ICMS: it may only
        transfer the credit stated under CSOSN 101/201 (LC 123/2006, art. 23,
        par. 1 and 2), which arrives in ``icmssn_credit_value``. Without that
        value there is no ICMS to credit, whatever the CST on the line says.

        Only ICMS is affected. PIS and COFINS credits of a non-cumulative
        buyer are taken at the buyer own rates and do not depend on the
        supplier regime (ADI SRF 15/2007).
        """
        self.ensure_one()
        partner = self.partner_id
        if not partner or partner.tax_framework not in TAX_FRAMEWORK_SIMPLES_ALL:
            return False
        return not self.icmssn_credit_value

    def _resolve_tax_creditability(self, tax_domain):
        """Whether this line may credit ``tax_domain``, and why.

        Three independent gates, all of which must allow the credit:

        1. the BUYER regime, which says whether this company takes credits
           of that tax at all;
        2. the DESTINATION of the goods, derived from the CFOP, which vetoes
           taxes the law does not let this destination recover;
        3. the NATURE of the operation, read from the line CST.
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
        "creditability_origin",
    )
    def _compute_taxes_creditable(self):
        """Derive the creditable flags from the three creditability gates.

        Computed (not onchange) so programmatic flows - purchase orders
        creating stock moves, imported fiscal documents - get the right
        creditability without any UI interaction.

        Lines whose creditability did not come from the rules are left
        alone. Without that check the compute would silently overwrite a
        decision the user took, on the next edit of any field it depends
        on, which is the opposite of giving the fiscal user the last word.

        The company fields are listed one by one because the regime gates
        read them: depending on ``company_id`` alone would only recompute
        when the line changes company, never when the company changes its
        own tax regime.
        """
        for record in self:
            if record.creditability_origin != "derived":
                continue
            for domain in CREDITABLE_TAX_DOMAINS:
                creditable = record._resolve_tax_creditability(domain)
                record[f"{domain}_tax_is_creditable"] = creditable

    def _get_stock_cost_tax_map(self):
        """Which taxes of this line are a credit and which are cost.

        The accounting side of the net cost needs the same answer the
        valuation uses, per tax, so the vendor bill can post the credit to
        the recoverable account and leave the rest inside the product line.
        Returning it from here is what keeps a single source of truth: the
        ledger and the stock layer cannot disagree, because both read this.

        :return: {tax_domain: 'credit' | 'cost'} for the domains whose
            creditability is derived. An undetermined line reports
            everything as cost, matching how it is valued.
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
        """The quantity the net cost is divided by.

        Each model naming its own quantity field overrides this: a stock
        move counts ``product_uom_qty``, a purchase order line counts
        ``product_qty``. Returning zero means this record cannot state a
        unit cost, and the compute leaves it at zero.
        """
        self.ensure_one()
        return self.product_uom_qty if hasattr(self, "product_uom_qty") else 0.0

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
        "creditability_origin",
        # `quantity` is the fiscal mixin field each model relates to its own
        # quantity, which is what _get_cost_unit_qty divides by.
        "quantity",
    )
    def _compute_cost_unit(self):
        """Subtract creditable taxes from the unit cost."""
        for record in self:
            record.cost_unit = 0
            quantity = record._get_cost_unit_qty()

            if record.fiscal_operation_line_id and quantity:
                # Withholdings are added back: _compute_fiscal_amounts already
                # deducted them from fiscal_amount_total, but a withholding is
                # a financial obligation of the buyer towards the tax
                # authority, not a reduction of what the goods cost. The
                # acquisition cost is the gross amount (CPC 16, item 11).
                price = record.fiscal_amount_total + record.amount_tax_withholding

                if not record.freight_value_to_stock:
                    price -= record.freight_value
                if not record.insurance_value_to_stock:
                    price -= record.insurance_value
                if not record.other_value_to_stock:
                    price -= record.other_value

                # An undetermined line takes no credit at all. Valuing it
                # gross is the conservative side: it may overstate inventory,
                # which is visible and correctable, instead of understating
                # it, which overstates profit and is escrituração incorreta.
                if record.creditability_origin != "undetermined":
                    for tax in record.fiscal_tax_ids:
                        creditable = getattr(
                            record, f"{tax.tax_domain}_tax_is_creditable", False
                        )
                        if creditable:
                            price -= getattr(record, f"{tax.tax_domain}_value", 0.0)

                # Simples Nacional supplier: the transferable CSOSN 101/201
                # credit (LC 123/2006, art. 23, par. 1 and 2) reduces the
                # buyer cost. Three conditions, all required by that article:
                # the buyer is not itself Simples, the credit was stated on
                # the document, and the goods go to resale or manufacturing
                # (par. 1 grants the credit only for those two destinations).
                # It is a highlighted credit, not part of the invoice total,
                # so it is deducted here.
                if (
                    record.icmssn_credit_value
                    and record.creditability_origin != "undetermined"
                    and record.company_id.tax_framework not in TAX_FRAMEWORK_SIMPLES_ALL
                    and record.cfop_id.type_move in CSOSN_CREDIT_DESTINATIONS
                ):
                    price -= record.icmssn_credit_value

                # ICMS relief (desoneração) is already removed from
                # fiscal_amount_total by _rm_fields_to_amount, so it must
                # not be subtracted again here.

                price_precision = self.env["decimal.precision"].precision_get(
                    "Product Price"
                )
                record.cost_unit = float_round(
                    (price / quantity), precision_digits=price_precision
                )
