# Copyright 2024 Engenere.one
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class IrActionsReport(models.Model):
    _inherit = "ir.actions.report"

    def _render_qweb_html(self, report_ref, res_ids, data=None):
        if report_ref == "main_template_danfe_account":
            return
        return super()._render_qweb_html(report_ref, res_ids, data=data)

    def _render_qweb_pdf(self, report_ref, res_ids, data=None):
        if report_ref not in ["main_template_danfe_account"]:
            return super()._render_qweb_pdf(report_ref, res_ids, data=data)

        nfe = self.env["account.move"].search([("id", "in", res_ids)])

        return self._render_danfe(nfe)

    def _render_danfe(self, nfe):
        return super()._render_danfe(nfe=nfe)
