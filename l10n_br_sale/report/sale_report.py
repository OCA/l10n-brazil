# Copyright (C) 2011  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models

from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    NFE_IND_PRES,
    NFE_IND_PRES_DEFAULT,
)


class SaleReport(models.Model):
    _name = "sale.report"
    _inherit = ["sale.report", "l10n_br_fiscal.report.mixin"]

    ind_pres = fields.Selection(
        selection=NFE_IND_PRES,
        string="Buyer Presence",
        default=NFE_IND_PRES_DEFAULT,
    )

    total_with_taxes = fields.Float(
        string="Total with Taxes",
        digits="Account",
    )

    def _fiscal_report_factor(self):
        """Same currency conversion the core applies to price_total."""
        return (
            f"1 / {self._case_value_or_one('s.currency_rate')}"
            f" * {self._case_value_or_one('currency_table.rate')}"
        )

    def _select_additional_fields(self):
        res = super()._select_additional_fields()
        factor = self._fiscal_report_factor()
        res.update(self._fiscal_report_select("l", "partner", factor=factor))
        res["ind_pres"] = "s.ind_pres"
        # price_total is already the fiscal total (IPI, ST, freight, insurance
        # and other costs included) net of the withholdings
        res["total_with_taxes"] = (
            f"SUM((l.price_total + COALESCE(l.amount_tax_withholding, 0))"
            f" * {factor})"
        )
        return res

    def _from_sale(self):
        return super()._from_sale() + self._fiscal_report_from("l")

    def _group_by_sale(self):
        res = super()._group_by_sale()
        res += f"""
            , s.ind_pres
            , {self._fiscal_report_group_by("l", "partner")}
        """
        return res
