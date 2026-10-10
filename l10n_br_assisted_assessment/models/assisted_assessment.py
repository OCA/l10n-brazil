# Copyright 2026 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging
import re
from calendar import monthrange
from datetime import date, datetime, time, timedelta

from markupsafe import Markup

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    FISCAL_OUT,
    SITUACAO_EDOC_AUTORIZADA,
)

from ..constants import (
    AVAILABILITY_DAY,
    AVAILABILITY_DAY_DERE,
    BOOKKEEPING_AWAITING,
    BOOKKEEPING_MATCH,
    BOOKKEEPING_ONLY_ERP,
    BOOKKEEPING_VALUE,
    DEADLINE_WARNING_DAYS,
    DIVERGENCE_CREDIT_DENIED,
    DIVERGENCE_MISSING_FISCO,
    DIVERGENCE_MISSING_LOCAL,
    DIVERGENCE_VALUE,
    LINE_CREDIT,
    LINE_DEBIT,
    OPEN_REQUEST_STATES,
    PER_APUR_RE,
    SERVICE_CREDITS,
    SERVICE_DEBITS,
    SERVICE_LINE_TYPE,
    SERVICE_TYPES,
    TRIBUTES,
)

_logger = logging.getLogger(__name__)

DIRECTION_DELIVERY = [
    ("pending", "Not Requested"),
    ("requested", "In Progress"),
    ("received", "Delivered"),
    ("none", "None in this Period"),
]


class AssistedAssessment(models.Model):
    _name = "l10n_br_assessment.period"
    _description = "IBS/CBS assisted assessment period"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "per_apur desc, tribute, id desc"

    name = fields.Char(compute="_compute_name", store=True)
    company_id = fields.Many2one(
        comodel_name="res.company",
        required=True,
        default=lambda self: self.env.company,
    )
    currency_id = fields.Many2one(related="company_id.currency_id", store=True)
    tribute = fields.Selection(
        selection=TRIBUTES,
        required=True,
        default="cbs",
        tracking=True,
    )
    per_apur = fields.Char(
        string="Assessment Period",
        required=True,
        help="Assessment period in the YYYY-MM format.",
    )
    date_from = fields.Date(
        string="Start Date", compute="_compute_period_dates", store=True
    )
    date_to = fields.Date(
        string="End Date", compute="_compute_period_dates", store=True
    )
    date_available = fields.Date(
        string="Presentation Date",
        compute="_compute_deadlines",
        store=True,
        help="Date by which the tax administration presents the assessment.",
    )
    date_deadline = fields.Date(
        string="Deadline",
        compute="_compute_deadlines",
        store=True,
        help="Last business day to confirm or adjust the assessment. It is also "
        "the due date of the payable balance.",
    )
    days_to_deadline = fields.Integer(compute="_compute_days_to_deadline")
    date_confirmed = fields.Date(readonly=True, copy=False)

    state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("requested", "Requested"),
            ("received", "Received"),
            ("reconciled", "Reconciled"),
            ("diverged", "Divergences Found"),
            ("confirmed", "Confirmed"),
            ("expired", "Expired"),
        ],
        string="Status",
        default="draft",
        required=True,
        tracking=True,
    )

    line_ids = fields.One2many(
        comodel_name="l10n_br_assessment.line",
        inverse_name="period_id",
        string="Assessment Lines",
    )
    request_ids = fields.Many2many(
        comodel_name="l10n_br_assessment.request",
        relation="l10n_br_assessment_period_request_rel",
        column1="period_id",
        column2="request_id",
        string="Delivered Requests",
        help="Requests that delivered data for this period. A single request can "
        "carry several periods, because the endpoints answer per taxpayer.",
    )
    origin_request_ids = fields.One2many(
        comodel_name="l10n_br_assessment.request",
        inverse_name="period_id",
        string="Opened Requests",
    )
    all_request_ids = fields.Many2many(
        comodel_name="l10n_br_assessment.request",
        compute="_compute_all_request_ids",
        string="Requests",
        help="Requests opened from this period together with the ones that "
        "delivered data for it.",
    )
    has_notified_request = fields.Boolean(compute="_compute_request_actions")
    has_downloaded_request = fields.Boolean(compute="_compute_request_actions")
    divergence_ids = fields.One2many(
        comodel_name="l10n_br_assessment.divergence",
        inverse_name="period_id",
        string="Divergences",
    )
    open_divergence_count = fields.Integer(compute="_compute_open_divergence_count")

    previous_balance = fields.Monetary(
        string="Recoverable Balance",
        help="Recoverable balance carried from previous periods, as considered by "
        "the tax administration.",
    )
    fisco_debit = fields.Monetary(compute="_compute_fisco_totals", store=True)
    fisco_credit = fields.Monetary(compute="_compute_fisco_totals", store=True)
    fisco_balance = fields.Monetary(compute="_compute_fisco_totals", store=True)
    local_debit = fields.Monetary(compute="_compute_local_totals")
    local_credit = fields.Monetary(compute="_compute_local_totals")
    local_balance = fields.Monetary(compute="_compute_local_totals")
    difference = fields.Monetary(compute="_compute_difference")
    local_awaiting_download = fields.Boolean(
        compute="_compute_local_awaiting_download",
        help="Booked totals already include every authorized document of the "
        "period. The comparison with the tax administration waits until each "
        "direction is downloaded or marked as absent.",
    )
    bookkeeping_line_ids = fields.One2many(
        comodel_name="l10n_br_assessment.bookkeeping.line",
        inverse_name="period_id",
        compute="_compute_bookkeeping_lines",
        string="Bookkeeping",
    )
    no_debits = fields.Boolean(
        string="No Debits in this Period",
        help="Mark when the tax administration has nothing to deliver for debits, "
        "so the period can be reconciled without that service.",
    )
    no_credits = fields.Boolean(
        string="No Credits in this Period",
        help="Mark when the tax administration has nothing to deliver for credits, "
        "so the period can be reconciled without that service.",
    )
    debit_delivery = fields.Selection(
        selection=DIRECTION_DELIVERY,
        string="Debits",
        compute="_compute_direction_delivery",
    )
    credit_delivery = fields.Selection(
        selection=DIRECTION_DELIVERY,
        string="Credits",
        compute="_compute_direction_delivery",
    )
    directions_ready = fields.Boolean(compute="_compute_direction_delivery")

    _sql_constraints = [
        (
            "period_tribute_company_uniq",
            "unique (company_id, tribute, per_apur)",
            "There is already an assessment for this company, tribute and period.",
        ),
    ]

    @api.constrains("per_apur")
    def _check_per_apur(self):
        for record in self:
            if not re.match(PER_APUR_RE, record.per_apur or ""):
                raise ValidationError(
                    _(
                        "The assessment period %s is not in the YYYY-MM format.",
                        record.per_apur,
                    )
                )

    @api.model
    def _get_or_create(self, company, tribute, per_apur):
        """Return the assessment of a period, creating it when needed.

        A single request carries several periods, including adjustments of past
        ones, so the periods it touches cannot be created by hand beforehand.
        """
        period = self.search(
            [
                ("company_id", "=", company.id),
                ("tribute", "=", tribute),
                ("per_apur", "=", per_apur),
            ],
            limit=1,
        )
        if period:
            return period
        return self.create(
            {
                "company_id": company.id,
                "tribute": tribute,
                "per_apur": per_apur,
            }
        )

    @api.depends("tribute", "per_apur")
    def _compute_name(self):
        for record in self:
            tribute = dict(TRIBUTES).get(record.tribute, "")
            record.name = f"{tribute} {record.per_apur or ''}".strip()

    @api.depends("per_apur")
    def _compute_period_dates(self):
        for record in self:
            record.date_from = record.date_to = False
            if not re.match(PER_APUR_RE, record.per_apur or ""):
                continue
            year, month = (int(part) for part in record.per_apur.split("-"))
            record.date_from = date(year, month, 1)
            record.date_to = date(year, month, monthrange(year, month)[1])

    @api.depends(
        "date_to",
        "company_id.assessment_dere_subject",
        "company_id.assessment_calendar_id",
    )
    def _compute_deadlines(self):
        for record in self:
            record.date_available = record.date_deadline = False
            if not record.date_to:
                continue
            following = record.date_to + timedelta(days=1)
            day = (
                AVAILABILITY_DAY_DERE
                if record.company_id.assessment_dere_subject
                else AVAILABILITY_DAY
            )
            record.date_available = following.replace(day=day)
            record.date_deadline = record._last_business_day(following)

    def _last_business_day(self, reference):
        """Return the last business day of the month holding ``reference``."""
        self.ensure_one()
        calendar = self.company_id.assessment_calendar_id
        candidate = reference.replace(
            day=monthrange(reference.year, reference.month)[1]
        )
        while not self._is_business_day(calendar, candidate):
            candidate -= timedelta(days=1)
        return candidate

    @staticmethod
    def _is_business_day(calendar, candidate):
        if calendar:
            # Leaves are stored as datetimes, so a plain date cannot be compared.
            return calendar.is_business_day(datetime.combine(candidate, time(12, 0)))
        return candidate.weekday() < 5

    @api.depends("date_deadline")
    def _compute_days_to_deadline(self):
        today = fields.Date.context_today(self)
        for record in self:
            record.days_to_deadline = (
                (record.date_deadline - today).days if record.date_deadline else 0
            )

    @api.depends("divergence_ids.state")
    def _compute_open_divergence_count(self):
        for record in self:
            record.open_divergence_count = len(
                record.divergence_ids.filtered(lambda line: line.state == "open")
            )

    @api.depends("origin_request_ids", "request_ids")
    def _compute_all_request_ids(self):
        for record in self:
            record.all_request_ids = record.origin_request_ids | record.request_ids

    @api.depends("origin_request_ids.state", "request_ids.state")
    def _compute_request_actions(self):
        for record in self:
            states = set(record._related_requests().mapped("state"))
            record.has_notified_request = "notified" in states
            record.has_downloaded_request = "downloaded" in states

    def _related_requests(self):
        self.ensure_one()
        return self.origin_request_ids | self.request_ids

    @api.depends("line_ids.value", "line_ids.line_type", "previous_balance")
    def _compute_fisco_totals(self):
        for record in self:
            debit = sum(
                record.line_ids.filtered(
                    lambda line: line.line_type == LINE_DEBIT
                ).mapped("value")
            )
            credit = sum(
                record.line_ids.filtered(
                    lambda line: line.line_type == LINE_CREDIT
                ).mapped("value")
            )
            record.fisco_debit = debit
            record.fisco_credit = credit
            record.fisco_balance = debit - credit - record.previous_balance

    @api.depends("date_from", "date_to", "previous_balance", "tribute", "company_id")
    def _compute_local_totals(self):
        for record in self:
            debit = credit = 0.0
            for line_type, values in record._local_values_by_key(
                [LINE_DEBIT, LINE_CREDIT]
            ).items():
                total = sum(values.values())
                if line_type == LINE_DEBIT:
                    debit = total
                else:
                    credit = total
            record.local_debit = debit
            record.local_credit = credit
            record.local_balance = debit - credit - record.previous_balance

    @api.depends("fisco_balance", "local_balance")
    def _compute_difference(self):
        for record in self:
            record.difference = record.fisco_balance - record.local_balance

    @api.depends(
        "debit_delivery",
        "credit_delivery",
        "no_debits",
        "no_credits",
        "directions_ready",
    )
    def _compute_local_awaiting_download(self):
        for record in self:
            record.local_awaiting_download = not record.directions_ready

    def _compared_line_types(self):
        """Directions that may produce missing-in-the-assessment divergences.

        A direction that has not been downloaded yet must not be reported as
        missing at the tax administration. Marking it as absent is enough.
        """
        self.ensure_one()
        types = set(self.line_ids.mapped("line_type"))
        if self.no_debits:
            types.add(LINE_DEBIT)
        if self.no_credits:
            types.add(LINE_CREDIT)
        return types

    @api.depends(
        "line_ids.line_type",
        "request_ids.service",
        "request_ids.state",
        "origin_request_ids.service",
        "origin_request_ids.state",
        "no_debits",
        "no_credits",
    )
    def _compute_direction_delivery(self):
        """Track each service on its own, apart from the period statusbar.

        Debits and credits are separate calls. The period status moves to
        Received on the first answer, so it cannot say whether the other
        direction is still missing.
        """
        for record in self:
            record.debit_delivery = record._direction_delivery(
                LINE_DEBIT, SERVICE_DEBITS, record.no_debits
            )
            record.credit_delivery = record._direction_delivery(
                LINE_CREDIT, SERVICE_CREDITS, record.no_credits
            )
            record.directions_ready = record.debit_delivery in (
                "received",
                "none",
            ) and record.credit_delivery in ("received", "none")

    def _direction_delivery(self, line_type, service, skipped):
        """Return how far one direction got for this period."""
        self.ensure_one()
        delivered = self.request_ids.filtered(
            lambda request: request.service == service and request.state == "done"
        )
        has_lines = self.line_ids.filtered(lambda line: line.line_type == line_type)
        if delivered or has_lines:
            return "received"
        pending = (self.origin_request_ids | self.request_ids).filtered(
            lambda request: request.service == service
            and request.state in OPEN_REQUEST_STATES
        )
        if pending:
            return "requested"
        if skipped:
            return "none"
        return "pending"

    def _assessed_line_types(self):
        """Return the line types already delivered by the tax administration.

        Debits and credits are separate services, so a direction that has not
        been downloaded yet must not produce divergences.
        """
        self.ensure_one()
        return set(self.line_ids.mapped("line_type"))

    def _assessed_values_by_key(self):
        """Aggregate the assessed value per direction and access key.

        The same document can produce several lines, one per origin, and all of
        them answer for the single value booked against that document.
        """
        self.ensure_one()
        grouped = {}
        for line in self.line_ids:
            entry = grouped.setdefault(
                (line.line_type, line.document_key),
                {"value": 0.0, "lines": self.env["l10n_br_assessment.line"]},
            )
            entry["value"] += line.value
            entry["lines"] |= line
        return grouped

    def _local_document_lines(self, line_types):
        self.ensure_one()
        if not self.date_from or not self.date_to:
            return self.env["l10n_br_fiscal.document.line"]
        operation_types = [
            FISCAL_OUT if line_type == LINE_DEBIT else "in" for line_type in line_types
        ]
        if not operation_types:
            return self.env["l10n_br_fiscal.document.line"]
        return self.env["l10n_br_fiscal.document.line"].search(
            [
                ("document_id.company_id", "=", self.company_id.id),
                ("document_id.state_edoc", "=", SITUACAO_EDOC_AUTORIZADA),
                ("document_id.document_key", "!=", False),
                (
                    "document_id.document_date",
                    ">=",
                    datetime.combine(self.date_from, time.min),
                ),
                (
                    "document_id.document_date",
                    "<=",
                    datetime.combine(self.date_to, time.max),
                ),
                ("document_id.fiscal_operation_type", "in", operation_types),
            ]
        )

    def _local_values_by_key(self, line_types=None):
        """Aggregate the booked tribute value per document access key.

        Returns a mapping of line type to ``{access key: value}``.
        """
        self.ensure_one()
        if line_types is None:
            line_types = self._assessed_line_types()
        result = {line_type: {} for line_type in line_types}
        value_field = f"{self.tribute}_value"
        for line in self._local_document_lines(line_types):
            document = line.document_id
            line_type = (
                LINE_DEBIT
                if document.fiscal_operation_type == FISCAL_OUT
                else LINE_CREDIT
            )
            if line_type not in result:
                continue
            key = document.document_key
            result[line_type][key] = result[line_type].get(key, 0.0) + (
                line[value_field] or 0.0
            )
        return result

    @api.depends(
        "date_from",
        "date_to",
        "tribute",
        "company_id",
        "line_ids.line_type",
        "line_ids.document_key",
        "line_ids.value",
        "no_debits",
        "no_credits",
    )
    def _compute_bookkeeping_lines(self):
        line_model = self.env["l10n_br_assessment.bookkeeping.line"]
        for record in self:
            if not record.id:
                record.bookkeeping_line_ids = line_model
                continue
            record.bookkeeping_line_ids = line_model.create(
                record._prepare_bookkeeping_vals()
            )

    def _prepare_bookkeeping_vals(self):
        """Return one row per authorized document of the period."""
        self.ensure_one()
        assessed = self._assessed_values_by_key()
        compared = self._compared_line_types()
        value_field = f"{self.tribute}_value"
        grouped = {}
        for line in self._local_document_lines([LINE_DEBIT, LINE_CREDIT]):
            document = line.document_id
            line_type = (
                LINE_DEBIT
                if document.fiscal_operation_type == FISCAL_OUT
                else LINE_CREDIT
            )
            entry = grouped.setdefault(document, {"line_type": line_type, "value": 0.0})
            entry["value"] += line[value_field] or 0.0
        vals_list = []
        for document, entry in grouped.items():
            fisco_entry = assessed.get((entry["line_type"], document.document_key))
            fisco_value = fisco_entry["value"] if fisco_entry else None
            status = self._bookkeeping_status(
                entry["line_type"], entry["value"], fisco_value, compared
            )
            vals_list.append(
                {
                    "period_id": self.id,
                    "document_id": document.id,
                    "line_type": entry["line_type"],
                    "expected_value": entry["value"],
                    "fisco_value": fisco_value or 0.0,
                    "status": status,
                }
            )
        return vals_list

    def _bookkeeping_status(self, line_type, expected_value, fisco_value, compared):
        """Return the row status of an ERP document against the assessment."""
        self.ensure_one()
        if line_type not in compared:
            return BOOKKEEPING_AWAITING
        if fisco_value is None:
            return BOOKKEEPING_ONLY_ERP
        tolerance = self.company_id.assessment_tolerance or 0.01
        if abs(expected_value - fisco_value) <= tolerance:
            return BOOKKEEPING_MATCH
        return BOOKKEEPING_VALUE

    def _upsert_lines(self, vals_list, service):
        """Merge the increment sent by the fisco into the stored lines.

        The assessment endpoints answer with the documents included or updated
        since the previous query, so a stored line must be updated in place and
        the ones absent from the increment must be kept.
        """
        self.ensure_one()
        line_type = SERVICE_LINE_TYPE.get(service)
        if not line_type:
            raise UserError(_("Service %s does not produce assessment lines.", service))
        stored = {line._natural_key(): line for line in self.line_ids}
        to_create = []
        updated = 0
        for vals in vals_list:
            vals = dict(vals, period_id=self.id, line_type=line_type)
            key = (line_type, vals.get("document_key"), vals.get("origin") or 0)
            line = stored.get(key)
            if line:
                if line._values_changed(vals):
                    line.write(vals)
                    updated += 1
            else:
                to_create.append(vals)
        self.env["l10n_br_assessment.line"].create(to_create)
        if not to_create and not updated:
            return True
        if self.state in ("confirmed", "expired"):
            self._notify_confirmed_increment(service, len(to_create), updated)
            return True
        if self.state in ("draft", "requested", "reconciled", "diverged"):
            self.state = "received"
        self.message_post(
            body=_(
                "%(service)s increment applied. New lines: %(created)s. "
                "Updated lines: %(updated)s.",
                service=self._service_label(service),
                created=len(to_create),
                updated=updated,
            )
        )
        return True

    def _service_label(self, service):
        services = dict(
            self.env["l10n_br_assessment.request"]
            ._fields["service"]
            ._description_selection(self.env)
        )
        return services.get(service, service)

    def _notify_confirmed_increment(self, service, created, updated):
        """Keep a confirmed period stable and ask the author to review it."""
        self.ensure_one()
        self.message_post(
            body=_(
                "The tax administration changed %(name)s after confirmation. "
                "New lines: %(created)s. Updated lines: %(updated)s.",
                name=self.name,
                created=created,
                updated=updated,
            )
        )
        self.activity_schedule(
            "mail.mail_activity_data_todo",
            user_id=self.create_uid.id or self.env.uid,
            summary=_(
                "Review the increment applied after confirmation of %s",
                self.name,
            ),
            note=_(
                "The tax administration sent new %(service)s data after this "
                "assessment was confirmed.",
                service=self._service_label(service),
            ),
        )
        return True

    def _notify_answer_without_data(self, request, periods):
        """Return the origin period to draft when the answer covered others."""
        self.ensure_one()
        if self.state == "requested":
            self.state = "draft"
        if periods:
            body = _(
                "Request %(request)s did not return data for this period. "
                "The answer covered %(periods)s.",
                request=request.name,
                periods=Markup(", ").join(
                    period._get_html_link() for period in periods
                ),
            )
        else:
            body = _(
                "Request %s did not return data for this period.",
                request.name,
            )
        self.message_post(body=body)
        return True

    def action_request_debits(self):
        return self._create_request(SERVICE_DEBITS)

    def action_request_credits(self):
        return self._create_request(SERVICE_CREDITS)

    def _create_request(self, service):
        self.ensure_one()
        self._check_open_request(service)
        request = self.env["l10n_br_assessment.request"].create(
            {
                "company_id": self.company_id.id,
                "tribute": self.tribute,
                "service": service,
                "period_id": self.id,
            }
        )
        request.action_transmit()
        if self.state == "draft":
            self.state = "requested"
        return request

    def _check_open_request(self, service):
        """Refuse a second opening while a previous call is still pending.

        The gateway charges every opening against the daily quota, so the
        pending request must be downloaded or applied first. A finished call
        does not block a later increment.
        """
        self.ensure_one()
        existing = self.env["l10n_br_assessment.request"].search(
            [
                ("company_id", "=", self.company_id.id),
                ("tribute", "=", self.tribute),
                ("service", "=", service),
                ("state", "in", OPEN_REQUEST_STATES),
            ],
            limit=1,
        )
        if existing:
            raise UserError(
                _(
                    "There is already an open %(service)s request for %(tribute)s. "
                    "Download or apply %(name)s before opening another one.",
                    service=dict(SERVICE_TYPES).get(service, service),
                    tribute=dict(TRIBUTES).get(self.tribute, self.tribute),
                    name=existing.name,
                )
            )
        return True

    def action_download_ready_requests(self):
        for record in self:
            record._related_requests().filtered(
                lambda request: request.state == "notified"
            ).action_download()
        return True

    def action_apply_downloaded_requests(self):
        for record in self:
            record._related_requests().filtered(
                lambda request: request.state == "downloaded"
            ).action_apply()
        return True

    def action_reconcile(self):
        for record in self:
            record._reconcile()
        return True

    def _reconcile(self):
        self.ensure_one()
        if self.state not in ("received", "reconciled", "diverged"):
            raise UserError(
                _("Download the assessment before reconciling %s.", self.name)
            )
        self.divergence_ids.filtered(lambda line: line.state == "open").unlink()
        stored = {line._natural_key(): line for line in self.divergence_ids}
        tolerance = self.company_id.assessment_tolerance or 0.01
        line_types = self._compared_line_types()
        local_values = self._local_values_by_key(line_types)
        assessed = self._assessed_values_by_key()
        divergence_model = self.env["l10n_br_assessment.divergence"]
        to_create = []
        for (line_type, key), group in assessed.items():
            booked = local_values.get(line_type, {})
            local_value = booked.get(key)
            fisco_value = group["value"]
            if local_value is None:
                vals = divergence_model._prepare_vals(
                    self,
                    DIVERGENCE_MISSING_LOCAL,
                    line_type,
                    key,
                    fisco_value,
                    0.0,
                    group["lines"][:1],
                )
                created = self._merge_divergence(stored, vals)
                if created:
                    to_create.append(created)
                continue
            if abs(local_value - fisco_value) <= tolerance:
                continue
            divergence_type = DIVERGENCE_VALUE
            if line_type == LINE_CREDIT and abs(fisco_value) <= tolerance:
                divergence_type = DIVERGENCE_CREDIT_DENIED
            vals = divergence_model._prepare_vals(
                self,
                divergence_type,
                line_type,
                key,
                fisco_value,
                local_value,
                group["lines"][:1],
            )
            created = self._merge_divergence(stored, vals)
            if created:
                to_create.append(created)
        for line_type, booked in local_values.items():
            if line_type not in line_types:
                continue
            for key, local_value in booked.items():
                if (line_type, key) in assessed:
                    continue
                if abs(local_value) <= tolerance:
                    continue
                vals = divergence_model._prepare_vals(
                    self,
                    DIVERGENCE_MISSING_FISCO,
                    line_type,
                    key,
                    0.0,
                    local_value,
                )
                created = self._merge_divergence(stored, vals)
                if created:
                    to_create.append(created)
        created = divergence_model.create(to_create)
        open_divergences = (
            self.divergence_ids.filtered(lambda line: line.state == "open") | created
        )
        self.state = "diverged" if open_divergences else "reconciled"
        return True

    def _merge_divergence(self, stored, vals):
        """Reuse a treated divergence or return vals to create a new one.

        A later increment can change the amounts, so a treated row is reopened
        when the figures no longer match what the user already reviewed.
        """
        self.ensure_one()
        key = (
            vals.get("line_type"),
            vals.get("document_key"),
            vals.get("divergence_type"),
        )
        existing = stored.get(key)
        if not existing:
            return vals
        if existing._values_changed(vals):
            existing.write(dict(vals, state="open"))
        return False

    def action_confirm(self):
        for record in self:
            record._confirm()
        return True

    def _confirm(self):
        self.ensure_one()
        if self.state not in ("reconciled", "diverged"):
            raise UserError(
                _("Reconcile %s before confirming the assessment.", self.name)
            )
        if self.open_divergence_count:
            raise UserError(
                _(
                    "%(name)s still has %(count)s open divergences. Handle or "
                    "ignore them before confirming, because confirming implies "
                    "acknowledgement of debt.",
                    name=self.name,
                    count=self.open_divergence_count,
                )
            )
        self.write(
            {"state": "confirmed", "date_confirmed": fields.Date.context_today(self)}
        )
        self.message_post(
            body=_(
                "Assessment confirmed. Confirming constitutes the tax credit and "
                "implies acknowledgement of debt."
            )
        )
        return True

    @api.model
    def _cron_check_deadlines(self):
        return self._check_deadlines(fields.Date.context_today(self))

    @api.model
    def _check_deadlines(self, today):
        periods = self.search(
            [
                ("state", "not in", ("confirmed", "expired")),
                ("date_deadline", "!=", False),
            ]
        )
        for period in periods:
            try:
                if period.date_deadline < today:
                    period._mark_expired()
                elif (period.date_deadline - today).days <= DEADLINE_WARNING_DAYS:
                    period._schedule_deadline_activity()
            except Exception:
                _logger.exception(
                    "Assisted assessment deadline check failed for period %s",
                    period.id,
                )
        return True

    def _mark_expired(self):
        self.ensure_one()
        self.state = "expired"
        self.message_post(
            body=_(
                "The deadline expired without confirmation. The balance presented "
                "by the tax administration is presumed correct and the tax credit "
                "is constituted."
            )
        )
        return True

    def _schedule_deadline_activity(self):
        self.ensure_one()
        summary = _("Review the assisted assessment of %s", self.name)
        existing = self.activity_ids.filtered(lambda act: act.summary == summary)
        if existing:
            return False
        self.activity_schedule(
            "mail.mail_activity_data_todo",
            date_deadline=self.date_deadline,
            summary=summary,
            note=_(
                "Confirm or adjust the assessment by %s. Without a manifestation "
                "the presented balance is presumed correct.",
                self.date_deadline,
            ),
        )
        return True
