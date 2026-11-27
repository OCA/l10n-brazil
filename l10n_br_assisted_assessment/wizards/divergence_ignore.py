# Copyright 2026 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, fields, models
from odoo.exceptions import UserError


class AssistedAssessmentDivergenceIgnore(models.TransientModel):
    _name = "l10n_br_assisted_assessment.divergence.ignore"
    _description = "Reason for ignoring an assessment divergence"

    divergence_id = fields.Many2one(
        comodel_name="l10n_br_assisted_assessment.divergence",
        required=True,
        readonly=True,
    )
    notes = fields.Text(
        string="Reason",
        required=True,
        help="Why the local review is closed without fixing this divergence.",
    )
    editing = fields.Boolean(readonly=True)

    def action_confirm(self):
        self.ensure_one()
        reason = (self.notes or "").strip()
        if not reason:
            raise UserError(
                _(
                    "Explain why this divergence is ignored before closing "
                    "the local review without fixing it."
                )
            )
        divergence = self.divergence_id
        values = {"notes": reason}
        if divergence.state != "ignored":
            values["state"] = "ignored"
        divergence.write(values)
        return {"type": "ir.actions.act_window_close"}
