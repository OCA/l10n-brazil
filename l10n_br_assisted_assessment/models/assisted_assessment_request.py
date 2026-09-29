# Copyright 2026 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging
from datetime import datetime, time

import pytz

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from ..constants import DAILY_REQUEST_QUOTA, SERVICE_TYPES, TRIBUTES

_logger = logging.getLogger(__name__)

PERIOD_REQUEST_REL = "l10n_br_assessment_period_request_rel"


class AssistedAssessmentRequest(models.Model):
    _name = "l10n_br_assessment.request"
    _description = "IBS/CBS assisted assessment asynchronous request"
    _order = "id desc"

    name = fields.Char(compute="_compute_name", store=True)
    company_id = fields.Many2one(
        comodel_name="res.company",
        required=True,
        default=lambda self: self.env.company,
    )
    currency_id = fields.Many2one(related="company_id.currency_id")
    tribute = fields.Selection(selection=TRIBUTES, required=True, default="cbs")
    service = fields.Selection(selection=SERVICE_TYPES, required=True)
    period_id = fields.Many2one(
        comodel_name="l10n_br_assessment.period",
        string="Requested From",
        ondelete="set null",
        help="Period the request was triggered from. The answer can carry other "
        "periods, since the endpoints answer per taxpayer.",
    )
    period_ids = fields.Many2many(
        comodel_name="l10n_br_assessment.period",
        relation=PERIOD_REQUEST_REL,
        column1="request_id",
        column2="period_id",
        string="Periods Delivered",
    )
    ticket = fields.Char(
        string="Request Ticket",
        help="Ticket returned when the request was opened, used to poll its "
        "status when the callback does not arrive.",
    )
    return_url = fields.Char(string="Callback URL")
    estimated_seconds = fields.Integer(
        help="Processing time estimated by the tax administration.",
    )
    delivered_line_count = fields.Integer(
        string="Delivered Lines",
        compute="_compute_delivered_totals",
        help="Lines this request delivered. Debits and credits are separate "
        "requests, so this is not the period balance.",
    )
    delivered_amount = fields.Monetary(
        compute="_compute_delivered_totals",
        help="Sum of the assessed values this request delivered for its own "
        "service. It is not the payable balance of the period.",
    )
    signed_url = fields.Char(
        string="Signed URL",
        groups="l10n_br_assisted_assessment.group_manager",
        help="Pre-signed download URL delivered by the callback. It authorises "
        "the download while valid and must be treated as a secret.",
    )
    signed_url_expires_at = fields.Datetime(string="Signed URL Expires At")
    payload = fields.Text(help="Raw payload downloaded from the tax administration.")
    response_text = fields.Text(string="Last Response")
    error_code = fields.Char()
    error_message = fields.Char()
    state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("requested", "Requested"),
            ("notified", "Ready to Download"),
            ("downloaded", "Downloaded"),
            ("done", "Applied"),
            ("error", "Error"),
        ],
        string="Status",
        default="draft",
        required=True,
    )
    request_date = fields.Datetime(readonly=True, copy=False)

    @api.depends("service", "tribute", "request_date")
    def _compute_name(self):
        services = dict(self._fields["service"]._description_selection(self.env))
        tributes = dict(self._fields["tribute"]._description_selection(self.env))
        for record in self:
            request_date = ""
            if record.request_date:
                request_date = fields.Datetime.to_string(
                    fields.Datetime.context_timestamp(record, record.request_date)
                )
            record.name = " ".join(
                part
                for part in (
                    tributes.get(record.tribute),
                    services.get(record.service),
                    request_date,
                )
                if part
            )

    def action_transmit(self):
        for request in self:
            request._check_quota()
            request._transmit()
            request.request_date = fields.Datetime.now()
        return True

    def _check_quota(self):
        """Guard the daily limit the gateway applies to the opening endpoint.

        A refused request is counted as well: it reached the endpoint, so it was
        charged. Only the ones that never got there, and therefore have no
        request date, are free.
        """
        self.ensure_one()
        start, end = self._quota_window()
        used = self.search_count(
            [
                ("id", "!=", self.id),
                ("company_id", "=", self.company_id.id),
                ("tribute", "=", self.tribute),
                ("service", "=", self.service),
                ("request_date", ">=", start),
                ("request_date", "<=", end),
            ]
        )
        if used >= DAILY_REQUEST_QUOTA:
            raise UserError(
                _(
                    "The daily quota of %(quota)s calls for the %(service)s "
                    "endpoint has been used. Try again tomorrow.",
                    quota=DAILY_REQUEST_QUOTA,
                    service=self.service,
                )
            )
        return True

    def _quota_window(self):
        """Return the UTC bounds of the local day the quota is counted in."""
        self.ensure_one()
        timezone = pytz.timezone(self.env.user.tz or "UTC")
        today = fields.Date.context_today(self)
        start = timezone.localize(datetime.combine(today, time.min)).astimezone(
            pytz.utc
        )
        end = timezone.localize(datetime.combine(today, time.max)).astimezone(pytz.utc)
        return start.replace(tzinfo=None), end.replace(tzinfo=None)

    def register_callback(self, payload):
        """Store what the tax administration sent to the callback URL."""
        self.ensure_one()
        if payload.get("codigoErro"):
            self.write(
                {
                    "state": "error",
                    "error_code": payload.get("codigoErro"),
                    "error_message": payload.get("mensagemErro"),
                }
            )
            return False
        expires_at = payload.get("urlAssinadaExpiraEm")
        self.write(
            {
                "state": "notified",
                "signed_url": payload.get("urlAssinada"),
                "signed_url_expires_at": self._parse_datetime(expires_at),
                "error_code": False,
                "error_message": False,
            }
        )
        return True

    @api.model
    def _parse_datetime(self, value):
        """Parse an ISO 8601 timestamp into a naive UTC datetime."""
        if not value:
            return False
        try:
            parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except ValueError:
            _logger.warning("Unparseable assessment timestamp %s", value)
            return False
        if parsed.tzinfo:
            parsed = parsed.astimezone(pytz.utc).replace(tzinfo=None)
        return parsed

    def action_check_status(self):
        for request in self:
            request._check_status()
        return True

    def _check_status(self):
        self.ensure_one()
        payload = self._fetch_status()
        self.response_text = str(payload)
        state = (payload.get("estado") or "").upper()
        if state == "CONCLUIDA":
            return self.register_callback(payload)
        if state == "ERRO":
            self.write(
                {
                    "state": "error",
                    "error_code": payload.get("codigoErro"),
                    "error_message": payload.get("mensagemErro"),
                }
            )
            return False
        return True

    def action_download(self):
        for request in self:
            request._download()
        return True

    def _download(self):
        self.ensure_one()
        if not self.signed_url:
            raise UserError(
                _("Request %s has no signed URL to download from.", self.name)
            )
        if (
            self.signed_url_expires_at
            and self.signed_url_expires_at < fields.Datetime.now()
        ):
            raise UserError(
                _(
                    "The signed URL of %s expired. Open a new request to get a "
                    "fresh one.",
                    self.name,
                )
            )
        self.write({"payload": self._fetch_payload(), "state": "downloaded"})
        return True

    @api.depends("payload", "state", "service")
    def _compute_delivered_totals(self):
        """Summarise the file of this request, not the period it landed on."""
        for request in self:
            count, amount = request._delivered_totals()
            request.delivered_line_count = count
            request.delivered_amount = amount

    def _delivered_totals(self):
        """Return ``(line count, assessed amount)`` carried by this request."""
        self.ensure_one()
        if self.state != "done" or not self.payload:
            return 0, 0.0
        try:
            parsed = self._parse_payload()
        except (NotImplementedError, UserError):
            return 0, 0.0
        count = 0
        amount = 0.0
        for vals_list in parsed.values():
            count += len(vals_list)
            amount += sum(vals.get("value") or 0.0 for vals in vals_list)
        return count, amount

    def action_apply(self):
        for request in self:
            request._apply()
        return True

    def _apply(self):
        self.ensure_one()
        if not self.payload:
            raise UserError(_("Request %s has no payload to apply.", self.name))
        period_model = self.env["l10n_br_assessment.period"]
        periods = period_model.browse()
        for per_apur, vals_list in self._parse_payload().items():
            period = period_model._get_or_create(
                self.company_id, self.tribute, per_apur
            )
            period._upsert_lines(vals_list, self.service)
            periods |= period
        self.write({"state": "done", "period_ids": [fields.Command.set(periods.ids)]})
        if self.period_id and self.period_id not in periods:
            self.period_id._notify_answer_without_data(self, periods)
        return True

    def _transmit(self):
        """Open the request at the tax administration.

        Implemented by the transport modules, since the CBS is served by the RFB
        and the IBS by the CGIBS.
        """
        self.ensure_one()
        raise UserError(
            _(
                "No transport module is installed for %s. Install the transport "
                "addon or import the payload manually.",
                (self.tribute or "").upper(),
            )
        )

    def _fetch_status(self):
        """Return the status payload of the request."""
        self.ensure_one()
        raise NotImplementedError("The transport module must implement _fetch_status.")

    def _fetch_payload(self):
        """Return the raw file the signed URL points to."""
        self.ensure_one()
        raise NotImplementedError("The transport module must implement _fetch_payload.")

    def _parse_payload(self):
        """Convert the raw payload into line values grouped by assessment period.

        Returns a mapping of ``YYYY-MM`` to a list of line values, because a
        single answer carries the current period along with adjustments of
        previous ones.
        """
        self.ensure_one()
        raise NotImplementedError("The transport module must implement _parse_payload.")
