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
        help="Effective tax of Simples Nacional, when the activity falls"
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
        "current_effective_tax",
        "current_range_id",
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
        for rec in self:
            range_id = rec.current_range_id
            rec.tax_icms_percent = rec.calculate_tax(range_id.tax_icms_percent)
            rec.tax_cpp_percent = rec.calculate_tax(range_id.tax_cpp_percent)
            rec.tax_csll_percent = rec.calculate_tax(range_id.tax_csll_percent)
            rec.tax_ipi_percent = rec.calculate_tax(range_id.tax_ipi_percent)
            rec.tax_irpj_percent = rec.calculate_tax(range_id.tax_irpj_percent)
            rec.tax_cofins_percent = rec.calculate_tax(range_id.tax_cofins_percent)
            rec.tax_pis_percent = rec.calculate_tax(range_id.tax_pis_percent)
            rec.tax_iss_percent = rec.calculate_tax(range_id.tax_iss_percent)

    def calculate_tax(self, x_tax_rate):
        self.ensure_one()
        effective_total_tax = self.current_effective_tax
        effective_x_tax = effective_total_tax * (x_tax_rate / 100)
        return round(effective_x_tax, 2)

    @api.depends("company_id", "company_id.annual_revenue", "current_range_id")
    def _compute_current_effective_tax(self):
        for record in self:
            annual_revenue = record.company_id.annual_revenue
            tax_range_id = record.current_range_id
            record.current_effective_tax = 0.0
            if not tax_range_id:
                return
            if annual_revenue:
                tax = annual_revenue * tax_range_id.total_tax_percent / 100
                tax = tax - tax_range_id.amount_deduced
                tax = tax / annual_revenue
                tax = tax * 100
                record.current_effective_tax = tax
            else:
                record.current_effective_tax = tax_range_id.total_tax_percent

    @api.depends(
        "company_id",
        "company_id.annual_revenue",
        "company_id.coefficient_r",
    )
    def _compute_current_range_id(self):
        for record in self:
            company_id = record.company_id
            tax_range = record.env["l10n_br_fiscal.simplified.tax.range"].search(
                [
                    ("simplified_tax_id", "=", record.simplified_tax_id.id),
                    ("inital_revenue", "<=", company_id.annual_revenue),
                    ("final_revenue", ">=", company_id.annual_revenue),
                ],
                limit=1,
            )
            record.current_range_id = tax_range
