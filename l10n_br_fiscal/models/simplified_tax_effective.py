# Copyright 2023 Engenere - Antônio S. Pereira Neto <neto@engenere.one>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class SimplifiedTaxEffective(models.Model):
    _name = "l10n_br_fiscal.simplified.tax.effective"
    _description = "Effective Tax Rate for Simples Nacional"

    _sql_constraints = [
        (
            "sn_effective_tax_unique",
            "unique (simplified_tax_id,company_id)",
            "There is already an effective tax line for this "
            "company and this Simples Nacional table",
        )
    ]

    simplified_tax_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.simplified.tax",
        string="Annex",
        help="Annex Tax Table of Simples Nacional",
        required=True,
    )

    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        ondelete="cascade",
    )

    current_range_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.simplified.tax.range",
        string="Range",
        help="Range into which the company falls based on current revenue.",
        compute="_compute_current_range_id",
        store=True,
    )

    current_effective_tax = fields.Float(
        string="Tax Rate %",
        help="Effective tax of Simples Nacional, when the activity falls "
        "under this annex, based on the current range.",
        digits="Fiscal Tax Percent",
        compute="_compute_current_effective_tax",
        store=True,
    )

    tax_icms_percent = fields.Float(
        string="ICMS %",
        digits="Fiscal Tax Percent",
        compute="_compute_tax_percent",
        store=True,
    )

    tax_cpp_percent = fields.Float(
        string="CPP %",
        digits="Fiscal Tax Percent",
        compute="_compute_tax_percent",
        store=True,
    )

    tax_csll_percent = fields.Float(
        string="CSLL %",
        digits="Fiscal Tax Percent",
        compute="_compute_tax_percent",
        store=True,
    )

    tax_ipi_percent = fields.Float(
        string="IPI %",
        digits="Fiscal Tax Percent",
        compute="_compute_tax_percent",
        store=True,
    )

    tax_iss_percent = fields.Float(
        string="ISS %",
        digits="Fiscal Tax Percent",
        compute="_compute_tax_percent",
        store=True,
    )

    tax_irpj_percent = fields.Float(
        string="IRPJ %",
        digits="Fiscal Tax Percent",
        compute="_compute_tax_percent",
        store=True,
    )

    tax_cofins_percent = fields.Float(
        string="COFINS %",
        digits="Fiscal Tax Percent",
        compute="_compute_tax_percent",
        store=True,
    )

    tax_pis_percent = fields.Float(
        string="PIS %",
        digits="Fiscal Tax Percent",
        compute="_compute_tax_percent",
        store=True,
    )

    @api.depends(
        "company_id.annual_revenue",
        "current_range_id",
        "current_range_id.total_tax_percent",
        "current_range_id.amount_deduced",
        "current_range_id.tax_icms_percent",
        "current_range_id.tax_cpp_percent",
        "current_range_id.tax_csll_percent",
        "current_range_id.tax_ipi_percent",
        "current_range_id.tax_irpj_percent",
        "current_range_id.tax_cofins_percent",
        "current_range_id.tax_pis_percent",
        "current_range_id.tax_iss_percent",
    )
    def _compute_tax_percent(self):
        tax_domains = ("icms", "cpp", "csll", "ipi", "irpj", "cofins", "pis", "iss")
        for rec in self:
            revenue = rec.company_id.annual_revenue
            for tax_domain in tax_domains:
                rec[
                    f"tax_{tax_domain}_percent"
                ] = rec.current_range_id._get_effective_tax_percent(revenue, tax_domain)

    @api.depends(
        "company_id.annual_revenue",
        "current_range_id",
        "current_range_id.total_tax_percent",
        "current_range_id.amount_deduced",
    )
    def _compute_current_effective_tax(self):
        for record in self:
            record.current_effective_tax = record.current_range_id._get_effective_tax(
                record.company_id.annual_revenue
            )

    @api.depends("simplified_tax_id", "company_id", "company_id.annual_revenue")
    def _compute_current_range_id(self):
        for record in self:
            record.current_range_id = record.simplified_tax_id._get_range(
                record.company_id.annual_revenue
            )
