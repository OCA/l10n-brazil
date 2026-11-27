# Copyright 2026 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, models
from odoo.exceptions import UserError

from odoo.addons.l10n_br_assisted_assessment.constants import TRIBUTE_CBS


class AssistedAssessment(models.Model):
    _inherit = "l10n_br_assisted_assessment.period"

    def action_open_cbs_suppliers(self):
        """Open this period's supplier board, rebuilt from the stored files."""
        self.ensure_one()
        if self.tribute != TRIBUTE_CBS:
            raise UserError(_("CBS suppliers are available on a CBS assessment."))
        suppliers = self.env["l10n_br_cbs_assisted_assessment.supplier"]
        suppliers._refresh(self)
        return suppliers._window_action(
            [("period_id", "=", self.id)],
            _("CBS Suppliers"),
        )
