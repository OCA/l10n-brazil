# Copyright (C) 2026-Today - KMEE (<https://kmee.com.br>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class PosOrderReport(models.Model):
    _name = "report.pos.order"
    _inherit = ["report.pos.order", "l10n_br_fiscal.report.mixin"]

    def _fiscal_report_factor(self):
        """Same currency conversion the core applies to price_total."""
        return (
            "1 / CASE COALESCE(s.currency_rate, 0)"
            " WHEN 0 THEN 1.0 ELSE s.currency_rate END"
        )

    def _select(self):
        res = self._fiscal_report_select(
            "l", "fiscal_report_partner", factor=self._fiscal_report_factor()
        )
        return super()._select() + "".join(
            f", {expr} AS {fname}" for fname, expr in res.items()
        )

    def _from(self):
        return (
            super()._from()
            + """
            LEFT JOIN res_partner fiscal_report_partner
                ON fiscal_report_partner.id = s.partner_id
            """
            + self._fiscal_report_from("l")
        )

    def _group_by(self):
        group_by = self._fiscal_report_group_by("l", "fiscal_report_partner")
        return f"{super()._group_by()}, {group_by}"
