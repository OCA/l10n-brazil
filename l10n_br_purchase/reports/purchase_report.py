# Copyright (C) 2020 - TODAY Renato Lima - Akretion
# Copyright (C) 2021 - TODAY Magno Costa - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models
from odoo.tools import SQL


class PurchaseReport(models.Model):
    _name = "purchase.report"
    _inherit = ["purchase.report", "l10n_br_fiscal.report.mixin"]

    total_with_taxes = fields.Float(
        string="Total with Taxes",
        digits="Account",
    )

    def _fiscal_report_factor(self):
        """Same currency conversion the core applies to price_total."""
        return (
            "1 / COALESCE(NULLIF(po.currency_rate, 0), 1.0)"
            " * account_currency_table.rate"
        )

    def _select(self):
        factor = self._fiscal_report_factor()
        res = self._fiscal_report_select("l", "partner", factor=factor)
        # price_total is already the fiscal total (IPI, ST, freight, insurance
        # and other costs included) net of the withholdings
        res["total_with_taxes"] = (
            f"SUM((l.price_total + COALESCE(l.amount_tax_withholding, 0))"
            f" * {factor})"
        )
        fiscal = "".join(f", {expr} AS {fname}" for fname, expr in res.items())
        return SQL("%s" + fiscal, super()._select())

    def _from(self):
        return SQL("%s" + self._fiscal_report_from("l"), super()._from())

    def _group_by(self):
        group_by = self._fiscal_report_group_by("l", "partner")
        return SQL("%s, " + group_by, super()._group_by())
