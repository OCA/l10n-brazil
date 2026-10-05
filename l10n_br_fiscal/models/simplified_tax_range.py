# Copyright (C) 2019  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models
from odoo.tools import float_round


class SimplifiedTaxRange(models.Model):
    _name = "l10n_br_fiscal.simplified.tax.range"
    _description = "National Simplified Tax Range"
    _order = "name asc"

    name = fields.Char(required=True)

    simplified_tax_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.simplified.tax", string="Simplified Tax"
    )

    currency_id = fields.Many2one(
        comodel_name="res.currency", string="Currency", required=True
    )

    amount_deduced = fields.Monetary(
        string="Amount to be Deducted",
        currency_field="currency_id",
        required=True,
    )

    inital_revenue = fields.Monetary(
        currency_field="currency_id",
    )

    final_revenue = fields.Monetary(
        currency_field="currency_id",
    )

    total_tax_percent = fields.Float(string="Tax Percent", digits="Fiscal Tax Percent")

    tax_cpp_percent = fields.Float(
        string="Tax CPP Percent", digits="Fiscal Tax Percent"
    )

    tax_csll_percent = fields.Float(
        string="Tax CSLL Percent", digits="Fiscal Tax Percent"
    )

    tax_ipi_percent = fields.Float(
        string="Tax IPI Percent", digits="Fiscal Tax Percent"
    )

    tax_icms_percent = fields.Float(
        string="Tax ICMS Percent", digits="Fiscal Tax Percent"
    )

    tax_iss_percent = fields.Float(
        string="Tax ISS Percent", digits="Fiscal Tax Percent"
    )

    tax_irpj_percent = fields.Float(
        string="Tax IRPJ Percent", digits="Fiscal Tax Percent"
    )

    tax_cofins_percent = fields.Float(
        string="Tax COFINS Percent", digits="Fiscal Tax Percent"
    )

    tax_pis_percent = fields.Float(
        string="Tax PIS Percent", digits="Fiscal Tax Percent"
    )

    tax_ibs_percent = fields.Float(
        string="Tax IBS Percent", digits="Fiscal Tax Percent"
    )

    tax_cbs_percent = fields.Float(
        string="Tax CBS Percent", digits="Fiscal Tax Percent"
    )

    def _get_effective_tax(self, revenue):
        """Effective tax rate (%) of the Simples Nacional for a company whose
        gross revenue of the last 12 months (RBT12) falls into this range::

            (RBT12 x nominal rate - amount to be deducted) / RBT12

        as defined by the LC 123/2006, art. 18, § 1º-A. Without revenue, which
        is the case of the first month of activity, it is the nominal rate.
        """
        if not self:
            return 0.0
        self.ensure_one()
        if not revenue:
            return self.total_tax_percent
        tax_amount = revenue * self.total_tax_percent / 100 - self.amount_deduced
        return tax_amount / revenue * 100

    def _get_effective_tax_percent(self, revenue, tax_domain):
        """Effective rate (%) of one of the taxes unified by the Simples
        Nacional: the effective tax rate times the share of that tax in the
        range (LC 123/2006, art. 18, § 1º-B).

        :param tax_domain: the tax, as in the tax_<tax_domain>_percent fields.
        """
        if not self:
            return 0.0
        share = self[f"tax_{tax_domain}_percent"]
        return float_round(
            self._get_effective_tax(revenue) * share / 100, precision_digits=2
        )
