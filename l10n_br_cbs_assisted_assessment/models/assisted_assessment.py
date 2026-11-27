# Copyright 2026 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from odoo.addons.l10n_br_assisted_assessment.constants import (
    OPEN_REQUEST_STATES,
    SERVICE_PAYMENTS,
    SERVICE_WITHHOLDINGS,
    TRIBUTE_CBS,
)
from odoo.addons.l10n_br_assisted_assessment.models.assisted_assessment import (
    DIRECTION_DELIVERY,
)


class AssistedAssessment(models.Model):
    _inherit = "l10n_br_assisted_assessment.period"

    payment_line_ids = fields.One2many(
        comodel_name="l10n_br_cbs_assisted_assessment.payment.line",
        inverse_name="period_id",
        string="Payment Lines",
    )
    payment_delivery = fields.Selection(
        selection=DIRECTION_DELIVERY,
        string="Payments",
        compute="_compute_payment_delivery",
        help="How far the payments request got. An open request shows in "
        "progress even after a previous file was applied, and it does not "
        "change the period status.",
    )
    withholding_delivery = fields.Selection(
        selection=DIRECTION_DELIVERY,
        string="Withholdings",
        compute="_compute_payment_delivery",
        help="How far the acquirer withholdings request got. An open request "
        "shows in progress even after a previous file was applied, and it "
        "does not change the period status.",
    )

    @api.depends(
        "tribute",
        "request_ids.service",
        "request_ids.state",
        "origin_request_ids.service",
        "origin_request_ids.state",
        "payment_line_ids.payment_id.service",
    )
    def _compute_payment_delivery(self):
        """Track DARF services the way debits and credits are tracked.

        A payment file does not move the period statusbar, so without these
        badges an open payments or withholdings request is invisible.
        """
        for period in self:
            period.payment_delivery = period._service_delivery(SERVICE_PAYMENTS)
            period.withholding_delivery = period._service_delivery(SERVICE_WITHHOLDINGS)

    def _service_delivery(self, service):
        """Return how far one DARF service got for this period.

        An open request wins over a file already applied, so a new call does
        not stay hidden behind Delivered.
        """
        self.ensure_one()
        if self.tribute != TRIBUTE_CBS:
            return False
        pending = (self.origin_request_ids | self.request_ids).filtered(
            lambda request: request.service == service
            and request.state in OPEN_REQUEST_STATES
        )
        if pending:
            return "requested"
        delivered = self.request_ids.filtered(
            lambda request: request.service == service and request.state == "done"
        )
        has_lines = self.payment_line_ids.filtered(
            lambda line: line.payment_id.service == service
        )
        if delivered or has_lines:
            return "received"
        return "pending"

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
