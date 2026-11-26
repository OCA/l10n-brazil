# Copyright 2026 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, fields, models
from odoo.exceptions import AccessError


class ResCompany(models.Model):
    _inherit = "res.company"

    cbs_assessment_mock_mode = fields.Boolean(
        string="CBS Assessment Mock",
        help="Answer CBS assessment requests from local files instead of "
        "calling the Receita Federal. Nothing is sent to the gateway.",
    )

    def write(self, vals):
        if "cbs_assessment_mock_mode" in vals and not self.env.su:
            if not self.env.user.has_group("l10n_br_assisted_assessment.group_manager"):
                raise AccessError(
                    _("Only assessment managers can change the CBS mock mode.")
                )
        return super().write(vals)
