# Copyright 2026 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AssistedAssessment(models.Model):
    _inherit = "l10n_br_assisted_assessment.period"

    cbs_assessment_mock_mode = fields.Boolean(
        string="CBS Mock",
        related="company_id.cbs_assessment_mock_mode",
        readonly=False,
        help="Answer CBS assessment requests of this company from local files. "
        "Nothing is sent to the Receita Federal.",
    )

    def action_generate_mock_files(self):
        """Open the wizard that prepares the next local assessment files."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Prepare CBS Mock Files",
            "res_model": "l10n_br_cbs_assisted_assessment.mock.generate",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_company_id": self.company_id.id,
                "default_period_id": self.id,
            },
        }
