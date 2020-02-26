# Copyright (C) 2019  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models
from odoo.addons import decimal_precision as dp


class SimplifiedTaxRange(models.Model):
    _name = "l10n_br_fiscal.simplified.tax.range"
    _description = "National Simplified Tax Range"
    _order = "name asc"

    name = fields.Char(string="Name", required=True)

    simplified_tax_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.simplified.tax",
        string="Simplified Tax ID")

    currency_id = fields.Many2one(
        comodel_name="res.currency",
        string="Currency",
        required=True)

    amount_deduced = fields.Monetary(
        string="Amount to be Deducted",
        currency_field="currency_id",
        default=0.00,
        digits=dp.get_precision("Fiscal Documents"),
        required=True)

    inital_revenue = fields.Monetary(
        string="Initial Revenue",
        currency_field="currency_id",
        default=0.00,
        digits=dp.get_precision("Fiscal Documents"))

    final_revenue = fields.Monetary(
        string="Final Revenue",
        currency_field="currency_id",
        default=0.00,
        digits=dp.get_precision("Fiscal Documents"))

    total_tax_percent = fields.Float(
        string="Tax Percent",
        default=0.00,
        digits=dp.get_precision("Fiscal Tax Percent"))

    tax_cpp_percent = fields.Float(
        string="Tax CPP Percent",
        default=0.00,
        digits=dp.get_precision("Fiscal Tax Percent"))

    tax_csll_percent = fields.Float(
        string="Tax CSLL Percent",
        default=0.00,
        digits=dp.get_precision("Fiscal Tax Percent"))

    tax_ipi_percent = fields.Float(
        string="Tax IPI Percent",
        default=0.00,
        digits=dp.get_precision("Fiscal Tax Percent"))

    tax_icms_percent = fields.Float(
        string="Tax ICMS Percent",
        default=0.00,
        digits=dp.get_precision("Fiscal Tax Percent"))

    tax_iss_percent = fields.Float(
        string="Tax ISS Percent",
        default=0.00,
        digits=dp.get_precision("Fiscal Tax Percent"))

    tax_irpj_percent = fields.Float(
        string="Tax IRPJ Percent",
        default=0.00,
        digits=dp.get_precision("Fiscal Tax Percent"))

    tax_cofins_percent = fields.Float(
        string="Tax COFINS Percent",
        default=0.00,
        digits=dp.get_precision("Fiscal Tax Percent"))

    tax_pis_percent = fields.Float(
        string="Tax PIS Percent",
        default=0.00,
        digits=dp.get_precision("Fiscal Tax Percent"))
