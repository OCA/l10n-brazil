# Copyright (C) 2019  Renato Lima - Akretion
# Copyright (C) 2020  Luis Felipe Mileo - KMEE
# Copyright (C) 2023  Antônio S. Pereira Neto - Engenere
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models


class SimplifiedTax(models.Model):
    _name = "l10n_br_fiscal.simplified.tax"
    _description = "National Simplified Tax"

    name = fields.Char(required=True)

    cnae_ids = fields.Many2many(
        comodel_name="l10n_br_fiscal.cnae",
        domain="[('internal_type', '=', 'normal')]",
        string="CNAEs",
    )

    simplified_tax_range_ids = fields.One2many(
        comodel_name="l10n_br_fiscal.simplified.tax.range",
        inverse_name="simplified_tax_id",
        string="Simplified Tax Range",
        copy=False,
    )

    coefficient_r = fields.Boolean(
        readonly=True,
    )

    # Rates of the annex for a company, the one given in the context or the
    # active one. Not stored: they follow the gross revenue of the company.
    current_range_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.simplified.tax.range",
        string="Range",
        help="Range of the annex the company falls into, given its gross "
        "revenue of the last 12 months.",
        compute="_compute_current_rates",
    )

    current_effective_tax = fields.Float(
        string="Tax Rate %",
        help="Effective tax rate of the annex for the company, in its range.",
        digits="Fiscal Tax Percent",
        compute="_compute_current_rates",
    )

    tax_irpj_percent = fields.Float(
        string="IRPJ %", digits="Fiscal Tax Percent", compute="_compute_current_rates"
    )

    tax_csll_percent = fields.Float(
        string="CSLL %", digits="Fiscal Tax Percent", compute="_compute_current_rates"
    )

    tax_cofins_percent = fields.Float(
        string="COFINS %", digits="Fiscal Tax Percent", compute="_compute_current_rates"
    )

    tax_pis_percent = fields.Float(
        string="PIS %", digits="Fiscal Tax Percent", compute="_compute_current_rates"
    )

    tax_cpp_percent = fields.Float(
        string="CPP %", digits="Fiscal Tax Percent", compute="_compute_current_rates"
    )

    tax_icms_percent = fields.Float(
        string="ICMS %", digits="Fiscal Tax Percent", compute="_compute_current_rates"
    )

    tax_iss_percent = fields.Float(
        string="ISS %", digits="Fiscal Tax Percent", compute="_compute_current_rates"
    )

    tax_ipi_percent = fields.Float(
        string="IPI %", digits="Fiscal Tax Percent", compute="_compute_current_rates"
    )

    @api.depends(
        "simplified_tax_range_ids.inital_revenue",
        "simplified_tax_range_ids.final_revenue",
        "simplified_tax_range_ids.total_tax_percent",
        "simplified_tax_range_ids.amount_deduced",
        "simplified_tax_range_ids.tax_irpj_percent",
        "simplified_tax_range_ids.tax_csll_percent",
        "simplified_tax_range_ids.tax_cofins_percent",
        "simplified_tax_range_ids.tax_pis_percent",
        "simplified_tax_range_ids.tax_cpp_percent",
        "simplified_tax_range_ids.tax_icms_percent",
        "simplified_tax_range_ids.tax_iss_percent",
        "simplified_tax_range_ids.tax_ipi_percent",
    )
    @api.depends_context("simplified_tax_company_id", "company")
    def _compute_current_rates(self):
        """Rates of each annex for the company given in the context, or the
        active one, computed by the same methods the tax engine uses."""
        company = self.env.company
        if "simplified_tax_company_id" in self.env.context:
            # a company not saved yet has no id and no revenue
            company = self.env["res.company"].browse(
                self.env.context["simplified_tax_company_id"]
            )
        revenue = company.annual_revenue
        tax_domains = ("irpj", "csll", "cofins", "pis", "cpp", "icms", "iss", "ipi")
        for annex in self:
            tax_range = annex._get_range(revenue)
            annex.current_range_id = tax_range
            annex.current_effective_tax = tax_range._get_effective_tax(revenue)
            for tax_domain in tax_domains:
                annex[
                    f"tax_{tax_domain}_percent"
                ] = tax_range._get_effective_tax_percent(revenue, tax_domain)

    def _get_range(self, revenue):
        """Range of the annex a gross revenue of the last 12 months falls into."""
        return self.simplified_tax_range_ids.filtered(
            lambda tax_range: tax_range.inital_revenue
            <= revenue
            <= tax_range.final_revenue
        )[:1]
