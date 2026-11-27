# Copyright 2026 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class AssistedAssessmentRequest(models.Model):
    _inherit = "l10n_br_assisted_assessment.request"

    def _transmit(self):
        """Tell the mock which period this opening belongs to.

        Without a prepared file the mock builds one on the fly. That file has
        to follow the period of the button, not the month of the clock.
        """
        period = self[:1].period_id
        if not period:
            return super()._transmit()
        return super(
            AssistedAssessmentRequest,
            self.with_context(cbs_assessment_mock_period_id=period.id),
        )._transmit()
