# Copyright 2026 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, fields, models
from odoo.exceptions import UserError

from odoo.addons.l10n_br_assisted_assessment.constants import (
    SERVICE_PAYMENTS,
    SERVICE_WITHHOLDINGS,
    TRIBUTE_CBS,
)


class AssistedAssessment(models.Model):
    _inherit = "l10n_br_assisted_assessment.period"

    payment_line_ids = fields.One2many(
        comodel_name="l10n_br_cbs_assisted_assessment.payment.line",
        inverse_name="period_id",
        string="Payment Lines",
    )

    def action_request_payments(self):
        """Open the consulta of payments that extinguished this CBS debit."""
        self._check_cbs_payment_request()
        return self._create_request(SERVICE_PAYMENTS)

    def action_request_withholdings(self):
        """Open the consulta of CBS collected by this company as acquirer."""
        self._check_cbs_payment_request()
        return self._create_request(SERVICE_WITHHOLDINGS)

    def _check_cbs_payment_request(self):
        for period in self:
            if period.tribute != TRIBUTE_CBS:
                raise UserError(
                    _(
                        "Payments and acquirer withholdings are served by the "
                        "CBS assessment APIs. %s is not a CBS period.",
                        period.display_name,
                    )
                )
        return True
