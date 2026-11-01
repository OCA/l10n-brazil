# Copyright 2026 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, models
from odoo.exceptions import UserError


class ReportDereRfbAssessment(models.AbstractModel):
    _name = "report.l10n_br_dere.report_dere_rfb_assessment"
    _description = "DeRE RFB assessment PDF"

    def _get_report_values(self, docids, data=None):
        docs = self.env["l10n_br_dere.declaration"].browse(docids)
        empty = docs.filtered(
            lambda doc: not doc.rfb_total_ids
            and not doc.rfb_mismatch
            and not doc.rfb_assessment_event_id
        )
        if empty:
            raise UserError(
                _("There is no RFB assessment to print for %s.")
                % ", ".join(empty.mapped("display_name"))
            )
        return {
            "doc_ids": docs.ids,
            "doc_model": "l10n_br_dere.declaration",
            "docs": docs,
        }
