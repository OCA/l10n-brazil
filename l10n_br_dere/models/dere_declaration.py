# Copyright 2026 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import calendar
import json
import logging
import re
from collections import defaultdict
from datetime import date, timedelta

import requests
from lxml import etree

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

from odoo.addons.l10n_br_dere_spec.models import xsd_validator

from ..constants import (
    CODTRIB_D1106,
    CODTRIB_D1121,
    D1199_RECEIPT_RE,
    DEDUCTION_DOCUMENT_EXCLUDED_STATES,
    DEFAULT_TP_ATIV_BY_REGIME,
    DEFAULT_VER_APLIC,
    DFE_TYPE_BY_DOCUMENT,
    EVENT_D1001,
    EVENT_D1011,
    EVENT_D1101,
    EVENT_D1106,
    EVENT_D1121,
    EVENT_D1198,
    EVENT_D1199,
    PERIODIC_EVENTS,
    PRIMARY_ACTIONS,
    PROTOCOL_RE,
    TABLE_EVENTS,
)
from . import xml_builder

_logger = logging.getLogger(__name__)


class DereDeclaration(models.Model):
    _name = "l10n_br_dere.declaration"
    _description = "DeRE monthly declaration"
    _inherit = [
        "mail.thread",
        "mail.activity.mixin",
        "l10n_br_dere.event.parent.mixin",
    ]
    _order = "per_apur desc, id desc"

    name = fields.Char(compute="_compute_name", store=True)
    company_id = fields.Many2one(
        comodel_name="res.company",
        required=True,
        default=lambda self: self.env.company,
        index=True,
    )
    per_apur = fields.Char(
        string="Assessment period",
        size=7,
        required=True,
        help="Format YYYY-MM.",
        tracking=True,
    )
    date_from = fields.Date(compute="_compute_period_dates", store=True)
    date_to = fields.Date(compute="_compute_period_dates", store=True)
    table_period_id = fields.Many2one(
        comodel_name="l10n_br_dere.table.period",
        compute="_compute_table_period_id",
        store=True,
        readonly=False,
        index=True,
    )
    ini_valid = fields.Date(
        related="table_period_id.ini_valid",
        string="Table validity start",
    )
    fim_valid = fields.Date(
        related="table_period_id.fim_valid",
        string="Table validity end",
    )
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("trial_ok", "Trial balance ready"),
            ("closed", "Closed"),
            ("reopened", "Reopened"),
        ],
        default="draft",
        required=True,
        tracking=True,
    )
    event_ids = fields.One2many(
        comodel_name="l10n_br_dere.event",
        inverse_name="declaration_id",
    )
    pgcc_account_ids = fields.One2many(
        related="table_period_id.pgcc_account_ids",
        readonly=True,
        help="Read-only snapshot of the table period. Edit PGCC on "
        "Fiscal → DeRE → Table Periods before D-1011 is accepted.",
    )
    trial_line_ids = fields.One2many(
        comodel_name="l10n_br_dere.trial.line",
        inverse_name="declaration_id",
    )
    reserve_line_ids = fields.One2many(
        comodel_name="l10n_br_dere.reserve.line",
        inverse_name="declaration_id",
    )
    deduction_line_ids = fields.One2many(
        comodel_name="l10n_br_dere.deduction.line",
        inverse_name="declaration_id",
    )
    batch_ids = fields.One2many(
        comodel_name="l10n_br_dere.batch",
        inverse_name="declaration_id",
    )
    ind_inexist_dedu = fields.Boolean(
        string="Declare no deductions",
        help="Only if the company is subject to D-1121 and has no deductions.",
    )
    subject_d1106 = fields.Boolean(
        related="company_id.dere_subject_d1106",
    )
    subject_d1121 = fields.Boolean(
        related="company_id.dere_subject_d1121",
    )
    can_discard_local_closing = fields.Boolean(
        string="Can discard local closing",
        compute="_compute_closing_actions",
    )
    can_discard_local_reopening = fields.Boolean(
        string="Can discard local reopening",
        compute="_compute_closing_actions",
    )
    can_reopen_period = fields.Boolean(
        string="Can reopen period",
        compute="_compute_closing_actions",
    )
    can_consult_results = fields.Boolean(
        string="Can consult results",
        compute="_compute_closing_actions",
    )
    can_generate_tables = fields.Boolean(
        string="Can generate tables",
        compute="_compute_closing_actions",
    )
    can_send_tables = fields.Boolean(
        string="Can send tables",
        compute="_compute_closing_actions",
    )
    can_generate_trial = fields.Boolean(
        string="Can generate trial balance",
        compute="_compute_closing_actions",
    )
    can_generate_d1106 = fields.Boolean(
        string="Can generate D-1106",
        compute="_compute_closing_actions",
    )
    can_load_deductions = fields.Boolean(
        string="Can load deductions",
        compute="_compute_closing_actions",
    )
    can_generate_d1121 = fields.Boolean(
        string="Can generate D-1121",
        compute="_compute_closing_actions",
    )
    can_close_period = fields.Boolean(
        string="Can close period",
        compute="_compute_closing_actions",
    )
    can_send_periodics = fields.Boolean(
        string="Can send periodics",
        compute="_compute_closing_actions",
    )
    can_replace_tables = fields.Boolean(compute="_compute_closing_actions")
    can_exclude_tables = fields.Boolean(compute="_compute_closing_actions")
    can_replace_trial = fields.Boolean(compute="_compute_closing_actions")
    can_exclude_trial = fields.Boolean(compute="_compute_closing_actions")
    can_replace_d1106 = fields.Boolean(compute="_compute_closing_actions")
    can_exclude_d1106 = fields.Boolean(compute="_compute_closing_actions")
    can_replace_d1121 = fields.Boolean(compute="_compute_closing_actions")
    can_exclude_d1121 = fields.Boolean(compute="_compute_closing_actions")
    can_rectify_d1121 = fields.Boolean(compute="_compute_closing_actions")
    primary_action = fields.Selection(
        selection=PRIMARY_ACTIONS,
        string="Primary action",
        compute="_compute_closing_actions",
    )

    _sql_constraints = [
        (
            "company_period_uniq",
            "unique(company_id, per_apur)",
            "There is already a DeRE declaration for this company and period.",
        )
    ]

    _IDENTITY_FIELDS = frozenset({"company_id", "per_apur"})
    _CLOSED_PROTECTED_FIELDS = frozenset(
        {
            "company_id",
            "per_apur",
            "ini_valid",
            "fim_valid",
            "table_period_id",
            "ind_inexist_dedu",
            "pgcc_account_ids",
            "trial_line_ids",
            "reserve_line_ids",
            "deduction_line_ids",
            "event_ids",
            "batch_ids",
        }
    )

    def write(self, vals):
        if not self.env.context.get("dere_force_declaration_write"):
            identity = set(vals) & self._IDENTITY_FIELDS
            if identity and self.filtered(lambda rec: rec.state != "draft"):
                raise UserError(
                    _(
                        "Company and period cannot be changed after the "
                        "declaration leaves draft."
                    )
                )
            protected = set(vals) & self._CLOSED_PROTECTED_FIELDS
            if protected and self.filtered(lambda rec: rec.state == "closed"):
                raise UserError(
                    _(
                        "Closed DeRE declarations cannot be modified. "
                        "Reopen the period first."
                    )
                )
        return super().write(vals)

    def unlink(self):
        locked = self.mapped("event_ids").filtered(
            lambda ev: ev.state not in ("draft", "generated")
        )
        if locked:
            raise UserError(
                _(
                    "Cannot delete a DeRE declaration after events were sent "
                    "or accepted. Exclude or rectify those events first."
                )
            )
        self.mapped("reserve_line_ids").with_context(
            dere_force_declaration_write=True
        ).unlink()
        self.mapped("trial_line_ids").with_context(
            dere_force_declaration_write=True
        ).unlink()
        self.mapped("deduction_line_ids").with_context(
            dere_force_declaration_write=True
        ).unlink()
        return super().unlink()

    @api.depends("company_id", "per_apur")
    def _compute_name(self):
        for rec in self:
            rec.name = f"DeRE {rec.per_apur or ''} / {rec.company_id.name or ''}"

    @api.depends("per_apur")
    def _compute_period_dates(self):
        for rec in self:
            rec.date_from = False
            rec.date_to = False
            if rec.per_apur and re.match(r"^20\d{2}-(0[1-9]|1[0-2])$", rec.per_apur):
                year, month = map(int, rec.per_apur.split("-"))
                last = calendar.monthrange(year, month)[1]
                rec.date_from = date(year, month, 1)
                rec.date_to = date(year, month, last)

    @api.depends("company_id", "date_to")
    def _compute_table_period_id(self):
        Table = self.env["l10n_br_dere.table.period"]
        for rec in self:
            rec.table_period_id = Table._find_covering(rec.company_id, rec.date_to)

    def _require_table_period(self):
        self.ensure_one()
        if self.table_period_id:
            return self.table_period_id
        if not self.date_from:
            raise UserError(
                _("Set a valid assessment period before generating tables.")
            )
        period = self.env["l10n_br_dere.table.period"]._get_or_create_for(
            self.company_id, self.date_from
        )
        self.table_period_id = period
        return period

    @api.constrains("per_apur")
    def _check_per_apur(self):
        for rec in self:
            if rec.per_apur and not re.match(
                r"^20\d{2}-(0[1-9]|1[0-2])$", rec.per_apur
            ):
                raise ValidationError(_("Assessment period must use the YYYY-MM mask."))

    def _header_vals(self, extra=None, event_type=None, tp_oper="1"):
        self.ensure_one()
        company = self.company_id
        extra = extra or {}
        extra = self._prepare_oper_extra(
            event_type, extra.get("tpOper") or tp_oper or "1", extra
        )
        tp_oper = extra.get("tpOper") or tp_oper or "1"
        vals = {
            "id": self.env["l10n_br_dere.event"]._generate_event_id(
                event_type=event_type,
                company=company,
                tp_amb=company.dere_tp_amb or "2",
            ),
            "tpOper": tp_oper,
            "tpAmb": company.dere_tp_amb or "2",
            "aplicEmi": "1",
            "verAplic": company.dere_ver_aplic or DEFAULT_VER_APLIC,
            "nrInsc": company._dere_cnpj_root(),
            "iniValid": fields.Date.to_string(self.ini_valid or self.date_from),
            "fimValid": fields.Date.to_string(self.fim_valid)
            if self.fim_valid
            else False,
            "perApur": self.per_apur,
        }
        vals.update(extra)
        if not vals["nrInsc"] or len(vals["nrInsc"]) != 8:
            raise UserError(_("Set a valid 8-digit CNPJ root on the company."))
        return vals

    def _event_records(self, event_type):
        self.ensure_one()
        if event_type in TABLE_EVENTS:
            if not self.table_period_id:
                return self.env["l10n_br_dere.event"]
            return self.table_period_id._event_records(event_type)
        return super()._event_records(event_type)

    def _latest_event(self, event_type):
        self.ensure_one()
        events = self._event_records(event_type)
        return events.sorted("id")[-1:]

    def _period_is_closed(self):
        return self.state == "closed"

    def _first_closing_accepted(self):
        closing = self._event_records(EVENT_D1199).filtered(
            lambda ev: ev.state == "accepted"
        )
        return bool(closing)

    @api.depends(
        "state",
        "event_ids.event_type",
        "event_ids.state",
        "event_ids.tp_oper",
        "batch_ids.state",
        "batch_ids.protocol",
        "table_period_id.can_generate_tables",
        "table_period_id.can_send_tables",
        "table_period_id.can_replace_tables",
        "table_period_id.can_exclude_tables",
        "table_period_id.can_consult_results",
        "table_period_id.event_ids.state",
        "subject_d1106",
        "subject_d1121",
        "ind_inexist_dedu",
        "deduction_line_ids",
    )
    def _compute_closing_actions(self):
        for rec in self:
            closing = rec._latest_event(EVENT_D1199)
            reopening = rec._latest_event(EVENT_D1198)
            # A local or transmitted D-1199 freezes the data it was built from.
            closing_pending = bool(
                closing and closing.state in ("draft", "generated", "sent")
            )
            rec.can_discard_local_closing = bool(
                closing and closing.state in ("draft", "generated")
            )
            rec.can_discard_local_reopening = bool(
                reopening and reopening.state in ("draft", "generated")
            )
            rec.can_reopen_period = rec.state == "closed" and bool(
                closing and closing.state == "accepted"
            )
            rec.can_consult_results = bool(
                rec.batch_ids.filtered(
                    lambda batch: batch.protocol and batch.state == "sent"
                )
                or rec.table_period_id.can_consult_results
            )
            tables = rec.table_period_id
            rec.can_generate_tables = rec.state != "closed" and (
                not tables or tables.can_generate_tables
            )
            rec.can_send_tables = rec.state != "closed" and bool(
                tables and tables.can_send_tables
            )
            rec.can_replace_tables = rec.state != "closed" and bool(
                tables and tables.can_replace_tables
            )
            rec.can_exclude_tables = rec.state != "closed" and bool(
                tables and tables.can_exclude_tables
            )
            rec.can_generate_trial = (
                rec.state
                in (
                    "draft",
                    "trial_ok",
                    "reopened",
                )
                and not closing_pending
                and bool(tables and tables.tables_accepted())
                and rec._can_include_event(EVENT_D1101)
            )
            rec.can_replace_trial = (
                rec.state in ("trial_ok", "reopened")
                and not closing_pending
                and rec._can_replace_or_exclude(EVENT_D1101)
            )
            rec.can_exclude_trial = rec.can_replace_trial
            rec.can_generate_d1106 = (
                rec.state in ("trial_ok", "reopened")
                and not closing_pending
                and rec._is_subject_d1106()
                and rec._has_d1106_codtrib()
                and rec._can_include_event(EVENT_D1106)
            )
            rec.can_replace_d1106 = (
                rec.state in ("trial_ok", "reopened")
                and not closing_pending
                and rec._is_subject_d1106()
                and rec._has_d1106_codtrib()
                and rec._can_replace_or_exclude(EVENT_D1106)
            )
            rec.can_exclude_d1106 = rec.can_replace_d1106
            rec.can_load_deductions = (
                rec.state in ("trial_ok", "reopened")
                and not closing_pending
                and rec._is_subject_d1121()
                # Loading contradicts the declared absence of deductions.
                and not rec.ind_inexist_dedu
                and (
                    rec._can_include_event(EVENT_D1121)
                    or rec._can_replace_or_exclude(EVENT_D1121)
                    or rec._can_rectify_d1121()
                )
            )
            rec.can_generate_d1121 = (
                rec.can_load_deductions
                and bool(rec.deduction_line_ids)
                and rec._can_include_event(EVENT_D1121)
            )
            rec.can_replace_d1121 = (
                rec.state in ("trial_ok", "reopened")
                and not closing_pending
                and rec._is_subject_d1121()
                and bool(rec.deduction_line_ids)
                and rec._can_replace_or_exclude(EVENT_D1121)
            )
            rec.can_exclude_d1121 = rec.can_replace_d1121
            rec.can_rectify_d1121 = (
                rec.state == "reopened"
                and not closing_pending
                and rec._is_subject_d1121()
                and bool(rec.deduction_line_ids)
                and rec._can_rectify_d1121()
            )
            rec.can_close_period = rec._can_prepare_closing()
            if rec.state in ("trial_ok", "reopened"):
                rec.can_send_periodics = bool(rec._next_events(PERIODIC_EVENTS))
            elif rec.state == "closed":
                # A closed period only transmits the reopening request.
                rec.can_send_periodics = bool(rec._next_events((EVENT_D1198,)))
            else:
                rec.can_send_periodics = False
            rec.primary_action = rec._next_primary_action()

    def _pgcc_codes(self):
        self.ensure_one()
        return set(filter(None, self.pgcc_account_ids.mapped("dere12_codTrib")))

    def _has_d1106_codtrib(self):
        self.ensure_one()
        return bool(self._pgcc_codes() & CODTRIB_D1106)

    def _is_subject_d1106(self):
        self.ensure_one()
        return self.company_id.dere_subject_d1106 or self._has_d1106_codtrib()

    def _is_subject_d1121(self):
        self.ensure_one()
        return self.company_id.dere_subject_d1121 or bool(
            self._pgcc_codes() & CODTRIB_D1121
        )

    def _can_rectify_d1121(self):
        self.ensure_one()
        reopening = self._latest_event(EVENT_D1198)
        return (
            self.state == "reopened"
            and self._first_closing_accepted()
            and reopening
            and reopening.state == "accepted"
        )

    def _event_can_be_generated(self, event_type):
        return self._can_include_event(event_type)

    def _event_needs_new_generation(self, event_type):
        self.ensure_one()
        latest = self._latest_event(event_type)
        if not latest or latest.state == "rejected":
            return self._can_include_event(event_type)
        if latest.state in ("sent", "accepted"):
            return self._can_include_event(event_type)
        return False

    def _needs_trial_after_reopening(self, trial):
        self.ensure_one()
        reopening = self._latest_event(EVENT_D1198)
        if not reopening or reopening.state != "accepted":
            return False
        if not trial:
            return True
        return trial.id < reopening.id

    def _can_prepare_closing(self):
        self.ensure_one()
        if self.state not in ("trial_ok", "reopened"):
            return False
        if not self._event_can_be_generated(EVENT_D1199):
            return False
        trial = self._latest_event(EVENT_D1101)
        if not trial or trial.tp_oper == "3" or not trial.xml_content:
            return False
        if self._needs_trial_after_reopening(trial):
            return False
        if self._has_d1106_codtrib():
            d1106 = self._latest_event(EVENT_D1106)
            if not d1106 or not d1106.xml_content or d1106.tp_oper == "3":
                return False
        if self._is_subject_d1121():
            if not self.deduction_line_ids:
                # Closing without loading deductions would silently declare their
                # absence, so wait for the load to confirm it.
                return self.ind_inexist_dedu
            d1121 = self._latest_event(EVENT_D1121)
            if not d1121 or not d1121.xml_content:
                return False
        return True

    def _next_primary_action(self):
        self.ensure_one()
        if self.can_consult_results:
            return "consult"
        if self.can_send_periodics:
            return "send_periodics"
        trial = self._latest_event(EVENT_D1101) or self._active_event(EVENT_D1101)
        if self.can_replace_trial and self._needs_trial_after_reopening(trial):
            return "replace_trial"
        if self.can_generate_trial and self._event_needs_new_generation(EVENT_D1101):
            return "generate_trial"
        if self.can_replace_d1106 and self._needs_trial_after_reopening(
            self._latest_event(EVENT_D1106) or self._active_event(EVENT_D1106)
        ):
            return "replace_d1106"
        if self.can_generate_d1106 and self._event_needs_new_generation(EVENT_D1106):
            return "generate_d1106"
        if self.can_rectify_d1121:
            return "rectify_d1121"
        if self.can_load_deductions and not self.deduction_line_ids:
            return "load_deductions"
        if self.can_generate_d1121 and self._event_needs_new_generation(EVENT_D1121):
            return "generate_d1121"
        if self.can_close_period and self._event_needs_new_generation(EVENT_D1199):
            return "close_period"
        if self.can_reopen_period:
            return "reopen"
        return False

    def _can_create_next_event(self, event_type):
        self.ensure_one()
        if event_type == EVENT_D1198:
            return self.state == "closed"
        if event_type in (EVENT_D1101, EVENT_D1106, EVENT_D1121, EVENT_D1199):
            latest = self._latest_event(EVENT_D1198)
            return bool(latest and latest.state == "accepted")
        return False

    def _get_or_create_event(self, event_type, tp_oper="1"):
        self.ensure_one()
        if event_type in (EVENT_D1198, EVENT_D1199):
            events = self.event_ids.filtered(lambda ev: ev.event_type == event_type)
            if events.filtered(
                lambda ev: ev.state in ("sent", "accepted")
            ) and not self._can_create_next_event(event_type):
                raise UserError(
                    _("D-1198 must be accepted before generating a new %s.")
                    % event_type
                )
            event = events.filtered(lambda ev: ev.state in ("draft", "generated"))[:1]
            if event:
                return event
            company = self.company_id
            return self.env["l10n_br_dere.event"].create(
                {
                    "declaration_id": self.id,
                    "event_type": event_type,
                    "tp_oper": "1",
                    "tp_amb": company.dere_tp_amb or "2",
                    "ver_aplic": company.dere_ver_aplic or DEFAULT_VER_APLIC,
                }
            )
        return self._create_oper_event(
            event_type, tp_oper=tp_oper, parent_field="declaration_id"
        )

    def _activity_codes(self, table_code):
        return self.company_id.dere_activity_ids.filtered(
            lambda act: act.table_code == table_code
        ).mapped("code")

    def action_generate_d1001(self):
        for rec in self:
            rec._generate_d1001()
        return True

    def _generate_d1001(self):
        self.ensure_one()
        return self._require_table_period()._generate_d1001()

    def action_generate_d1011(self):
        for rec in self:
            rec._generate_d1011()
        return True

    def _account_name_for_xml(self, record):
        """Return the account or group name in the company language for XML."""
        self.ensure_one()
        lang = self.company_id.partner_id.lang or "en_US"
        name = record.with_context(lang=lang).name or record.name or ""
        return name[:100]

    def _pgcc_row_from_group(self, group, codes):
        return self._require_table_period()._pgcc_row_from_group(group, codes)

    def _sync_pgcc_from_accounts(self):
        self.ensure_one()
        return self._require_table_period()._sync_pgcc_from_accounts()

    def _generate_d1011(self):
        self.ensure_one()
        return self._require_table_period()._generate_d1011()

    def action_generate_tables(self):
        for rec in self:
            rec._require_table_period().action_generate_tables()
        return True

    def action_replace_tables(self):
        self.ensure_one()
        return self._require_table_period().action_replace_tables()

    def action_exclude_tables(self):
        self.ensure_one()
        return self._require_table_period().action_exclude_tables()

    def action_send_tables(self):
        result = True
        for rec in self:
            action = rec._require_table_period().action_send_tables()
            if isinstance(action, dict):
                result = action
        return result

    def _reset_months(self, freq):
        mapping = {
            "A": {1},
            "S": {1, 7},
            "Q": {1, 5, 9},
            "T": {1, 4, 7, 10},
            "B": {1, 3, 5, 7, 9, 11},
            "M": set(range(1, 13)),
        }
        return mapping.get(freq or "M", {1})

    def _cycle_start(self, freq, date_from):
        year = date_from.year
        month = date_from.month
        starts = {
            "A": [1],
            "S": [1, 7],
            "Q": [1, 5, 9],
            "T": [1, 4, 7, 10],
            "B": [1, 3, 5, 7, 9, 11],
            "M": list(range(1, 13)),
        }
        candidates = [value for value in starts.get(freq or "M", [1]) if value <= month]
        return date(year, candidates[-1] if candidates else 1, 1)

    def _previous_trial_closing(self):
        previous = self._previous_declaration()
        return {
            line.pgcc_account_id.account_id.id: (
                line.dere12_vSaldoFinal
                if line.dere12_natSaldoFinal == "D"
                else -line.dere12_vSaldoFinal
            )
            for line in previous.trial_line_ids
            if line.pgcc_account_id.account_id
        }

    def _account_balances(self):
        self.ensure_one()
        AccountMoveLine = self.env["account.move.line"]
        domain_base = [
            ("company_id", "=", self.company_id.id),
            ("parent_state", "=", "posted"),
            ("account_id", "in", self.pgcc_account_ids.account_id.ids),
            ("display_type", "not in", ("line_section", "line_note")),
        ]
        opening = defaultdict(lambda: 0.0)
        opening_cycle = defaultdict(lambda: 0.0)
        period = defaultdict(
            lambda: {
                "debit": 0.0,
                "credit": 0.0,
                "ajuste_debt": 0.0,
                "ajuste_cred": 0.0,
            }
        )
        freq = self.company_id.dere_freq_encerr or "M"
        cycle_start = (
            self._cycle_start(freq, self.date_from) if self.date_from else False
        )
        prev_closing = self._previous_trial_closing()
        if self.date_from:
            for account, balance in AccountMoveLine._read_group(
                domain_base + [("date", "<", self.date_from)],
                groupby=["account_id"],
                aggregates=["balance:sum"],
            ):
                opening[account.id] = balance or 0.0
            if cycle_start:
                for account, balance in AccountMoveLine._read_group(
                    domain_base
                    + [
                        ("date", ">=", cycle_start),
                        ("date", "<", self.date_from),
                    ],
                    groupby=["account_id"],
                    aggregates=["balance:sum"],
                ):
                    opening_cycle[account.id] = balance or 0.0
        period_domain = domain_base
        if self.date_from:
            period_domain = period_domain + [("date", ">=", self.date_from)]
        if self.date_to:
            period_domain = period_domain + [("date", "<=", self.date_to)]
        for account, debit, credit in AccountMoveLine._read_group(
            period_domain,
            groupby=["account_id"],
            aggregates=["debit:sum", "credit:sum"],
        ):
            values = period[account.id]
            values["debit"] = debit or 0.0
            values["credit"] = credit or 0.0
        for account, debit, credit in AccountMoveLine._read_group(
            period_domain + [("move_id.reversed_entry_id", "!=", False)],
            groupby=["account_id"],
            aggregates=["debit:sum", "credit:sum"],
        ):
            values = period[account.id]
            values["ajuste_cred"] = debit or 0.0
            values["ajuste_debt"] = credit or 0.0
        return opening, opening_cycle, period, prev_closing, cycle_start

    def action_generate_d1101(self):
        for rec in self:
            rec._generate_d1101()
        return True

    def action_replace_d1101(self):
        for rec in self:
            rec._generate_d1101(tp_oper="2")
        return True

    def action_exclude_d1101(self):
        return self._action_event_operation(EVENT_D1101, "3")

    def _trial_opening(
        self, pgcc, opening, opening_cycle, prev_closing, month, reset_months
    ):
        if pgcc.dere12_codNat in ("4", "5"):
            if month in reset_months:
                return 0.0
            return opening_cycle[pgcc.account_id.id]
        if pgcc.account_id.id in prev_closing:
            return prev_closing[pgcc.account_id.id]
        return opening[pgcc.account_id.id]

    def _trial_vapur(self, nature, debit, credit, ajuste_debt, ajuste_cred):
        if nature == "D":
            return max(debit - ajuste_debt + ajuste_cred, 0.0)
        return max(credit - ajuste_cred + ajuste_debt, 0.0)

    def _generate_d1101(self, tp_oper=None, extra=None):
        self.ensure_one()
        tp_oper = tp_oper or self._default_periodic_tp_oper(EVENT_D1101)
        extra = self._prepare_oper_extra(EVENT_D1101, tp_oper, extra)
        if tp_oper == "3":
            vals = self._header_vals(extra, event_type=EVENT_D1101, tp_oper=tp_oper)
            event = self._get_or_create_event(EVENT_D1101, tp_oper=tp_oper)
            vals["id"] = event.event_id_attr or vals["id"]
            event.write(
                {
                    "event_id_attr": vals["id"],
                    "tp_oper": tp_oper,
                    "mot_excl": extra.get("motExcl"),
                }
            )
            event._store_xml(xml_builder.build_d1101(vals, []))
            return event
        if not self.pgcc_account_ids:
            self._sync_pgcc_from_accounts()
        opening, opening_cycle, period, prev_closing, _cycle_start = (
            self._account_balances()
        )
        month = int(self.per_apur.split("-")[1])
        reset_months = self._reset_months(self.company_id.dere_freq_encerr)
        self.trial_line_ids.unlink()
        rows = []
        for pgcc in self.pgcc_account_ids.filtered(
            lambda acc: acc.dere12_indCta == "A"
        ):
            values = period[pgcc.account_id.id]
            debit = values["debit"]
            credit = values["credit"]
            ajuste_debt = values["ajuste_debt"]
            ajuste_cred = values["ajuste_cred"]
            open_bal = self._trial_opening(
                pgcc, opening, opening_cycle, prev_closing, month, reset_months
            )
            close_bal = open_bal + debit - credit
            if not any((open_bal, debit, credit, close_bal)):
                continue
            nat_inic = "D" if open_bal > 0 else "C" if open_bal < 0 else "D"
            if abs(close_bal) < 0.005:
                nat_final = nat_inic
            else:
                nat_final = "D" if close_bal > 0 else "C"
            nature = (
                pgcc.dere12_natCta if pgcc.dere12_natCta in ("D", "C") else nat_final
            )
            v_apur = self._trial_vapur(nature, debit, credit, ajuste_debt, ajuste_cred)
            rows.append(
                {
                    "declaration_id": self.id,
                    "pgcc_account_id": pgcc.id,
                    "dere12_natSaldoInic": nat_inic,
                    "dere12_vSaldoInic": abs(open_bal),
                    "dere12_vMovDebt": abs(debit),
                    "dere12_vAjusteDebt": abs(ajuste_debt) or False,
                    "dere12_vMovCred": abs(credit),
                    "dere12_vAjusteCred": abs(ajuste_cred) or False,
                    "dere12_natSaldoFinal": nat_final,
                    "dere12_vSaldoFinal": abs(close_bal),
                    "dere12_natVApur": nature if v_apur else False,
                    "dere12_vApur": v_apur,
                }
            )
        if not rows:
            raise UserError(_("No analytic DeRE movement found for this period."))
        self.env["l10n_br_dere.trial.line"].create(rows)
        vals = self._header_vals(extra, event_type=EVENT_D1101, tp_oper=tp_oper)
        event = self._get_or_create_event(EVENT_D1101, tp_oper=tp_oper)
        vals["id"] = event.event_id_attr or vals["id"]
        event.write(
            {
                "event_id_attr": vals["id"],
                "tp_oper": tp_oper,
                "nr_recibo_prev": self._active_event(EVENT_D1011).nr_recibo,
            }
        )
        event._store_xml(
            xml_builder.build_d1101(
                vals, [line._to_xml_vals() for line in self.trial_line_ids]
            )
        )
        if self.state != "reopened":
            # A reopened period keeps its state until the new closing is accepted.
            self.state = "trial_ok"
        return event

    def _previous_period(self):
        self.ensure_one()
        if not self.per_apur or "-" not in self.per_apur:
            return False
        year, month = map(int, self.per_apur.split("-"))
        if month == 1:
            return f"{year - 1}-12"
        return f"{year}-{month - 1:02d}"

    def _previous_declaration(self):
        """Return the immediately previous month when its D-1101 is accepted.

        CONFERIR_SALDO_INICIAL needs that month's vSaldoFinal. A draft or
        skipped period must not seed the opening; the general ledger is used
        instead.
        """
        self.ensure_one()
        previous_period = self._previous_period()
        if not previous_period:
            return self.browse()
        previous = self.search(
            [
                ("company_id", "=", self.company_id.id),
                ("per_apur", "=", previous_period),
                ("id", "!=", self.id),
            ],
            limit=1,
        )
        if not previous:
            return self.browse()
        trial = previous._latest_event(EVENT_D1101)
        if trial and trial.state == "accepted":
            return previous
        return self.browse()

    def _reserve_opening(self, asset, prev_by_id, opening, one_to_one):
        prev = prev_by_id.get(asset.id_ativo)
        if prev:
            return prev.dere12_vSaldoFinal
        if one_to_one:
            return abs(opening.get(asset.account_id.id, 0.0))
        return 0.0

    def _reserve_counterpart_income(self, account):
        self.ensure_one()
        MoveLine = self.env["account.move.line"]
        reserve_lines = MoveLine.search(
            [
                ("move_id.company_id", "=", self.company_id.id),
                ("parent_state", "=", "posted"),
                ("account_id", "=", account.id),
                ("move_id.date", ">=", self.date_from),
                ("move_id.date", "<=", self.date_to),
                ("display_type", "not in", ("line_section", "line_note")),
            ]
        )
        move_ids = reserve_lines.mapped("move_id").ids
        received = 0.0
        redeemed = 0.0
        if move_ids:
            income_lines = MoveLine.search(
                [
                    ("move_id", "in", move_ids),
                    ("account_id.account_type", "=", "income"),
                    ("account_id", "!=", account.id),
                    ("display_type", "not in", ("line_section", "line_note")),
                ]
            )
            for income in income_lines:
                amount = income.credit - income.debit
                if amount <= 0.005:
                    continue
                move_reserve = reserve_lines.filtered(
                    lambda line, current=income: line.move_id == current.move_id
                )
                if sum(move_reserve.mapped("debit")) >= sum(
                    move_reserve.mapped("credit")
                ):
                    received += amount
                else:
                    redeemed += amount
        mapped = account.l10n_br_dere_reserve_income_account_id
        if mapped:
            extra_domain = [
                ("move_id.company_id", "=", self.company_id.id),
                ("parent_state", "=", "posted"),
                ("account_id", "=", mapped.id),
                ("move_id.date", ">=", self.date_from),
                ("move_id.date", "<=", self.date_to),
                ("display_type", "not in", ("line_section", "line_note")),
            ]
            if move_ids:
                extra_domain.append(("move_id", "not in", move_ids))
            extra = MoveLine.search(extra_domain)
            received += sum(extra.mapped("credit")) - sum(extra.mapped("debit"))
        return received, redeemed

    def _reserve_gl_vals(self, asset, opening, period, prev_by_id, one_to_one):
        vals = {
            "dere12_vSaldoInic": self._reserve_opening(
                asset, prev_by_id, opening, one_to_one
            ),
            "dere12_vVarMensal": 0.0,
            "dere12_vPrincLiqResg": 0.0,
            "dere12_vRendPerReceb": 0.0,
            "dere12_vRendLiqResg": 0.0,
        }
        if self.env.context.get("dere_skip_reserve_gl") or not one_to_one:
            return vals
        account_period = period.get(asset.account_id.id) or {
            "debit": 0.0,
            "credit": 0.0,
        }
        vals["dere12_vVarMensal"] = account_period["debit"]
        vals["dere12_vPrincLiqResg"] = account_period["credit"]
        received, redeemed = self._reserve_counterpart_income(asset.account_id)
        vals["dere12_vRendPerReceb"] = received
        vals["dere12_vRendLiqResg"] = redeemed
        return vals

    def _sync_reserve_lines_from_assets(self):
        self.ensure_one()
        assets = self.env["l10n_br_dere.reserve.asset"].search(
            [("company_id", "=", self.company_id.id), ("active", "=", True)]
        )
        if not self.pgcc_account_ids:
            self._sync_pgcc_from_accounts()
        pgcc_by_account = {line.account_id.id: line for line in self.pgcc_account_ids}
        previous = self._previous_declaration()
        prev_by_id = {line.dere12_idAtivo: line for line in previous.reserve_line_ids}
        asset_count_by_account = {}
        for asset in assets:
            asset_count_by_account[asset.account_id.id] = (
                asset_count_by_account.get(asset.account_id.id, 0) + 1
            )
        opening, _opening_cycle, period, _prev, _cycle = self._account_balances()
        existing = {line.dere12_idAtivo: line for line in self.reserve_line_ids}
        for asset in assets:
            pgcc = pgcc_by_account.get(asset.account_id.id)
            if not pgcc or pgcc.dere12_indCta != "A":
                raise UserError(
                    _(
                        "Technical-reserve asset %s must use an analytic "
                        "account mapped on the PGCC."
                    )
                    % asset.id_ativo
                )
            one_to_one = asset_count_by_account.get(asset.account_id.id) == 1
            gl_vals = self._reserve_gl_vals(
                asset, opening, period, prev_by_id, one_to_one
            )
            line_vals = {
                "asset_id": asset.id,
                "dere12_idAtivo": asset.id_ativo,
                "dere12_descAtivo": asset.desc_ativo,
                "pgcc_account_id": pgcc.id,
                "dere12_cCta": pgcc.dere12_cCta,
                **gl_vals,
            }
            existing_line = existing.get(asset.id_ativo)
            if existing_line:
                if one_to_one and not self.env.context.get("dere_skip_reserve_gl"):
                    existing_line.write(line_vals)
                continue
            line_vals["declaration_id"] = self.id
            self.env["l10n_br_dere.reserve.line"].create(line_vals)
        return self.reserve_line_ids

    def action_generate_d1106(self):
        for rec in self:
            rec._generate_d1106()
        return True

    def action_replace_d1106(self):
        for rec in self:
            rec._generate_d1106(tp_oper="2")
        return True

    def action_exclude_d1106(self):
        return self._action_event_operation(EVENT_D1106, "3")

    def _generate_d1106(self, tp_oper=None, extra=None):
        self.ensure_one()
        if not self._is_subject_d1106():
            raise UserError(_("The company is not subject to D-1106."))
        if self.state not in ("trial_ok", "reopened", "closed"):
            raise UserError(_("Generate the trial balance before D-1106."))
        tp_oper = tp_oper or self._default_periodic_tp_oper(EVENT_D1106)
        extra = self._prepare_oper_extra(EVENT_D1106, tp_oper, extra)
        if tp_oper == "3":
            vals = self._header_vals(extra, event_type=EVENT_D1106, tp_oper=tp_oper)
            event = self._get_or_create_event(EVENT_D1106, tp_oper=tp_oper)
            vals["id"] = event.event_id_attr or vals["id"]
            event.write(
                {
                    "event_id_attr": vals["id"],
                    "tp_oper": tp_oper,
                    "mot_excl": extra.get("motExcl"),
                }
            )
            event._store_xml(xml_builder.build_d1106(vals, []))
            return event
        if not self._has_d1106_codtrib():
            raise UserError(
                _(
                    "D-1106 inclusion or replacement requires a PGCC account "
                    "with a D-1106 taxation code."
                )
            )
        self._sync_reserve_lines_from_assets()
        if self.reserve_line_ids:
            extra["semAplic"] = False
            lines = [line._to_xml_vals() for line in self.reserve_line_ids]
        else:
            extra["semAplic"] = "1"
            lines = []
        vals = self._header_vals(extra, event_type=EVENT_D1106, tp_oper=tp_oper)
        event = self._get_or_create_event(EVENT_D1106, tp_oper=tp_oper)
        vals["id"] = event.event_id_attr or vals["id"]
        event.write({"event_id_attr": vals["id"], "tp_oper": tp_oper})
        event._store_xml(xml_builder.build_d1106(vals, lines))
        return event

    def _default_tp_ativ(self, operation=None):
        self.ensure_one()
        if operation and operation.l10n_br_dere_tp_ativ:
            return operation.l10n_br_dere_tp_ativ
        return DEFAULT_TP_ATIV_BY_REGIME.get(self.company_id.dere_reg_trib_princ or "")

    def _dfe_type_from_document(self, document):
        return DFE_TYPE_BY_DOCUMENT.get(document.document_type or "")

    def _inbound_deduction_documents(self):
        self.ensure_one()
        return self.env["l10n_br_fiscal.document"].search(
            [
                ("company_id", "=", self.company_id.id),
                ("fiscal_operation_type", "=", "in"),
                ("fiscal_operation_id.l10n_br_dere_deductible", "=", True),
                ("state_edoc", "not in", DEDUCTION_DOCUMENT_EXCLUDED_STATES),
                ("document_date", ">=", self.date_from),
                ("document_date", "<", self.date_to + timedelta(days=1)),
                ("document_key", "!=", False),
            ]
        )

    def _deduction_vals_from_document(self, document):
        self.ensure_one()
        tp_dfe = self._dfe_type_from_document(document)
        tp_ativ = self._default_tp_ativ(document.fiscal_operation_id)
        if not tp_dfe:
            raise UserError(
                _("Unsupported fiscal document type %s for D-1121.")
                % (document.document_type or document.display_name)
            )
        if not tp_ativ:
            raise UserError(
                _(
                    "Set the DeRE deduction activity on the fiscal operation "
                    "or use a health-care / prize-contest regime."
                )
            )
        amount = document.fiscal_amount_total or 0.0
        issue_date = fields.Date.to_date(document.document_date)
        issue_month = fields.Date.to_string(issue_date)[:7] if issue_date else False
        vals = {
            "declaration_id": self.id,
            "document_id": document.id,
            "dere12_tpDFe": tp_dfe,
            "dere12_chDFe": (document.document_key or "").replace(" ", "").upper(),
            "dere12_dtEmi": issue_date,
            "dere12_tpAtiv": tp_ativ,
            "dere12_vOper": amount,
            "dere12_vDed": amount,
        }
        if issue_month == self.per_apur:
            vals["dere12_vDedTotal"] = amount
        return vals

    def action_load_deductions(self):
        empty = self.env["l10n_br_dere.declaration"]
        for rec in self:
            if not rec._load_deductions():
                empty |= rec
        if empty == self:
            return self._notify_and_reload(
                _("No deductible document"),
                _(
                    "No deductible fiscal document was found for the period. "
                    "The declaration now reports the absence of deductions."
                ),
            )
        return True

    def _load_deductions(self):
        self.ensure_one()
        if not self._is_subject_d1121():
            raise UserError(_("The company is not subject to D-1121."))
        if self.state not in ("trial_ok", "reopened"):
            raise UserError(_("Generate the trial balance before loading deductions."))
        self.deduction_line_ids.unlink()
        rows = [
            self._deduction_vals_from_document(document)
            for document in self._inbound_deduction_documents()
        ]
        if rows:
            self.env["l10n_br_dere.deduction.line"].create(rows)
            if self.ind_inexist_dedu:
                self.ind_inexist_dedu = False
        elif not self.ind_inexist_dedu:
            # Without documents the period can only be closed as deduction-free.
            self.ind_inexist_dedu = True
        return self.deduction_line_ids

    def _ensure_deduction_items(self, line):
        if not line._needs_items():
            return
        if line.item_ids:
            return
        document = line.document_id
        if not document:
            raise UserError(
                _(
                    "Deduction %s has vDedTotal lower than vOper and needs "
                    "item breakdown."
                )
                % (line.dere12_chDFe or line.id)
            )
        items = []
        for index, fiscal_line in enumerate(document.fiscal_line_ids, start=1):
            n_item = False
            if "nfe40_nItem" in fiscal_line._fields and fiscal_line.nfe40_nItem:
                n_item = str(fiscal_line.nfe40_nItem)
            items.append(
                {
                    "line_id": line.id,
                    "dere12_nItem": n_item or str(index),
                    "dere12_vItem": fiscal_line.fiscal_amount_total or 0.0,
                    "dere12_vItemDedTotal": fiscal_line.fiscal_amount_total or 0.0,
                    "dere12_vItemDed": fiscal_line.fiscal_amount_total or 0.0,
                }
            )
        if not items:
            raise UserError(
                _("Fiscal document %s has no lines to build D-1121 items.")
                % line.dere12_chDFe
            )
        self.env["l10n_br_dere.deduction.item"].create(items)

    def _assert_deduction_current_account(self, line):
        issue_month = line._issue_period()
        if issue_month == self.per_apur:
            return
        if line.dere12_vDedTotal:
            raise UserError(
                _("Do not set vDedTotal after the issue month of key %s.")
                % line.dere12_chDFe
            )
        previous = self.search(
            [
                ("company_id", "=", self.company_id.id),
                ("per_apur", "<", self.per_apur),
                ("deduction_line_ids.dere12_chDFe", "=", line.dere12_chDFe),
            ],
            limit=1,
        )
        if not previous:
            raise UserError(
                _(
                    "Key %s must be opened in its issue month before later "
                    "D-1121 deductions."
                )
                % line.dere12_chDFe
            )

    def action_generate_d1121(self):
        for rec in self:
            rec._generate_d1121()
        return True

    def action_replace_d1121(self):
        for rec in self:
            rec._generate_d1121(tp_oper="2")
        return True

    def action_exclude_d1121(self):
        return self._action_event_operation(EVENT_D1121, "3")

    def action_rectify_d1121(self):
        return self._action_event_operation(EVENT_D1121, "4")

    def _generate_d1121(self, tp_oper=None, extra=None, lines=None):
        self.ensure_one()
        if not self._is_subject_d1121():
            raise UserError(_("The company is not subject to D-1121."))
        if self.state not in ("trial_ok", "reopened", "closed"):
            raise UserError(_("Generate the trial balance before D-1121."))
        tp_oper = tp_oper or self._default_periodic_tp_oper(EVENT_D1121)
        extra = self._prepare_oper_extra(EVENT_D1121, tp_oper, extra)
        if tp_oper == "3":
            vals = self._header_vals(extra, event_type=EVENT_D1121, tp_oper=tp_oper)
            event = self._get_or_create_event(EVENT_D1121, tp_oper=tp_oper)
            vals["id"] = event.event_id_attr or vals["id"]
            event.write(
                {
                    "event_id_attr": vals["id"],
                    "tp_oper": tp_oper,
                    "mot_excl": extra.get("motExcl"),
                }
            )
            event._store_xml(xml_builder.build_d1121(vals, []))
            return event
        if tp_oper == "4" and not extra.get("finEvt"):
            raise UserError(_("D-1121 rectification requires finEvt."))
        if self.ind_inexist_dedu:
            raise UserError(
                _("Do not generate D-1121 when the no-deductions flag is set.")
            )
        deduction_lines = lines or self.deduction_line_ids
        if not deduction_lines:
            raise UserError(_("Load or enter D-1121 deductions before generating."))
        for line in deduction_lines:
            self._assert_deduction_current_account(line)
            self._ensure_deduction_items(line)
        payload = []
        for line in deduction_lines:
            item = line._to_xml_vals()
            if tp_oper == "4" and extra.get("finEvt") in ("2", "3"):
                item["chDFeRetif"] = item.get("chDFe")
                item.pop("tpDFe", None)
                item.pop("chDFe", None)
            payload.append(item)
        vals = self._header_vals(extra, event_type=EVENT_D1121, tp_oper=tp_oper)
        event = self._get_or_create_event(EVENT_D1121, tp_oper=tp_oper)
        vals["id"] = event.event_id_attr or vals["id"]
        event.write({"event_id_attr": vals["id"], "tp_oper": tp_oper})
        event._store_xml(xml_builder.build_d1121(vals, payload))
        return event

    def _action_event_operation(self, event_type, tp_oper):
        self.ensure_one()
        wizard = self.env["l10n_br_dere.event.operation.wizard"].create(
            {
                "declaration_id": self.id,
                "event_type": event_type,
                "tp_oper": tp_oper,
                "fin_evt": "1" if tp_oper == "4" else False,
            }
        )
        return {
            "type": "ir.actions.act_window",
            "name": _("DeRE event operation"),
            "res_model": "l10n_br_dere.event.operation.wizard",
            "res_id": wizard.id,
            "view_mode": "form",
            "target": "new",
        }

    def action_generate_d1199(self):
        for rec in self:
            rec._generate_d1199()
        return True

    def _assert_d1199_prerequisites(self):
        self.ensure_one()
        if self.state not in ("trial_ok", "reopened", "closed"):
            raise UserError(_("Generate the trial balance before closing."))
        trial = self._latest_event(EVENT_D1101)
        if not trial or trial.tp_oper == "3" or not trial.xml_content:
            raise UserError(_("D-1101 must exist before D-1199."))
        if self._needs_trial_after_reopening(trial):
            raise UserError(
                _("Replace the trial balance after reopening before closing.")
            )
        if self._has_d1106_codtrib():
            d1106 = self._latest_event(EVENT_D1106)
            if not d1106 or not d1106.xml_content or d1106.tp_oper == "3":
                raise UserError(_("Generate D-1106 before closing."))
        self._assert_d1106_matches_trial()
        self._assert_pgcc_receipt_matches_trial()

    def _assert_d1106_matches_trial(self):
        self.ensure_one()
        if not self.reserve_line_ids:
            return
        trial = {
            line.dere12_cCta: line.dere12_vSaldoFinal for line in self.trial_line_ids
        }
        totals = defaultdict(float)
        for line in self.reserve_line_ids:
            totals[line.dere12_cCta] += line.dere12_vSaldoFinal
        mismatches = [
            code
            for code, total in totals.items()
            if abs(total - (trial.get(code) or 0.0)) > 0.005
        ]
        if mismatches:
            raise UserError(
                _("D-1106 closing balances must match D-1101 for accounts: %s")
                % ", ".join(sorted(mismatches))
            )

    def _assert_pgcc_receipt_matches_trial(self):
        self.ensure_one()
        trial = self._latest_event(EVENT_D1101)
        if trial and trial.tp_oper == "3":
            trial = self.env["l10n_br_dere.event"]
        pgcc = self._active_event(EVENT_D1011)
        if trial and pgcc and trial.nr_recibo_prev and pgcc.nr_recibo:
            if trial.nr_recibo_prev != pgcc.nr_recibo:
                raise UserError(
                    _(
                        "The D-1011 receipt used by D-1101 no longer matches the "
                        "chart of accounts in force."
                    )
                )

    def _d1199_info_vals(self):
        self.ensure_one()
        extra = {}
        d1121 = self._latest_event(EVENT_D1121)
        if self.ind_inexist_dedu and self.deduction_line_ids:
            raise UserError(
                _("Do not set the no-deductions flag when D-1121 lines exist.")
            )
        if self.ind_inexist_dedu and d1121 and d1121.xml_content:
            raise UserError(
                _("Do not set the no-deductions flag when D-1121 was generated.")
            )
        if self.ind_inexist_dedu:
            if not self._is_subject_d1121():
                raise UserError(
                    _(
                        "Do not set the no-deductions flag if the company is "
                        "not subject to D-1121."
                    )
                )
            extra["indInexistDedu"] = "1"
        elif self._is_subject_d1121() and self.deduction_line_ids:
            if not d1121 or not d1121.xml_content:
                raise UserError(_("Generate D-1121 before closing."))
        elif self._is_subject_d1121():
            self.ind_inexist_dedu = True
            extra["indInexistDedu"] = "1"
        return extra

    def _generate_d1199(self):
        self.ensure_one()
        self._assert_d1199_prerequisites()
        extra = self._d1199_info_vals()
        vals = self._header_vals(extra, event_type=EVENT_D1199)
        event = self._get_or_create_event(EVENT_D1199)
        vals["id"] = event.event_id_attr or vals["id"]
        event.event_id_attr = vals["id"]
        event._store_xml(xml_builder.build_d1199(vals))
        if self.state == "closed" and event.state in ("draft", "generated"):
            self.state = "trial_ok"
        return event

    def action_discard_local_closing(self):
        for rec in self:
            rec._discard_local_closing()
        return True

    def _discard_local_closing(self):
        self.ensure_one()
        closing = self._latest_event(EVENT_D1199)
        if not closing:
            raise UserError(_("There is no local D-1199 to discard."))
        if closing.state in ("sent", "accepted"):
            raise UserError(
                _("An official D-1199 cannot be discarded. Reopen the period.")
            )
        closing.unlink()
        if self.state == "closed":
            self.state = "trial_ok"
        return True

    def action_mark_reopened(self):
        for rec in self:
            rec._generate_d1198()
        return True

    def _d1199_reopen_receipt(self):
        self.ensure_one()
        closing = self._latest_event(EVENT_D1199)
        receipt = (closing.nr_recibo or "").strip() if closing else ""
        expected = (self.per_apur or "").replace("-", "")
        if (
            not closing
            or closing.state != "accepted"
            or not re.fullmatch(D1199_RECEIPT_RE, receipt)
            or receipt[:4] != "1199"
            or receipt[5:11] != expected
        ):
            raise UserError(
                _(
                    "Reopening requires an accepted D-1199 receipt "
                    "1199-%s-... for this period."
                )
                % expected
            )
        return receipt

    def _generate_d1198(self):
        self.ensure_one()
        if self.state not in ("closed", "reopened"):
            raise UserError(_("Only a closed period can be reopened."))
        vals = self._header_vals(
            {"nrReciboReab": self._d1199_reopen_receipt()},
            event_type=EVENT_D1198,
        )
        event = self._get_or_create_event(EVENT_D1198)
        vals["id"] = event.event_id_attr or vals["id"]
        event.event_id_attr = vals["id"]
        event._store_xml(xml_builder.build_d1198(vals))
        if self.state == "reopened" and event.state in ("draft", "generated"):
            self.state = "closed"
        return event

    def action_discard_local_reopening(self):
        for rec in self:
            rec._discard_local_reopening()
        return True

    def _discard_local_reopening(self):
        self.ensure_one()
        reopening = self._latest_event(EVENT_D1198)
        if not reopening:
            raise UserError(_("There is no local D-1198 to discard."))
        if reopening.state in ("sent", "accepted"):
            raise UserError(
                _("An official D-1198 cannot be discarded. The period stays reopened.")
            )
        reopening.unlink()
        if self.state == "reopened":
            self.state = "closed"
        return True

    def _require_processing_receipt(self, event_type, message):
        event = self._latest_event(event_type)
        if not event or not event.nr_recibo:
            raise UserError(message)
        return event

    def _assert_d1121_send_order(self):
        self._require_processing_receipt(
            EVENT_D1101,
            _("D-1101 processing receipt is required before sending D-1121."),
        )
        if self._has_d1106_codtrib():
            self._require_processing_receipt(
                EVENT_D1106,
                _("D-1106 processing receipt is required before sending D-1121."),
            )

    def _assert_d1199_send_order(self):
        d1101 = self._latest_event(EVENT_D1101)
        if not d1101:
            raise UserError(_("D-1101 must exist before D-1199."))
        if not d1101.nr_recibo:
            raise UserError(
                _("D-1101 processing receipt is required before sending D-1199.")
            )
        if self._has_d1106_codtrib():
            self._require_processing_receipt(
                EVENT_D1106,
                _("D-1106 processing receipt is required before sending D-1199."),
            )
        d1121 = self._latest_event(EVENT_D1121)
        if d1121 and d1121.xml_content and not d1121.nr_recibo:
            raise UserError(
                _("D-1121 processing receipt is required before sending D-1199.")
            )

    def _assert_send_order(self, event_types):
        self.ensure_one()
        types = set(event_types)
        if len(types) > 1:
            raise UserError(_("Send one DeRE event type per batch."))
        if types & set(TABLE_EVENTS) and types & set(PERIODIC_EVENTS):
            raise UserError(
                _("Do not send table events and periodic events in the same batch.")
            )
        if EVENT_D1011 in types:
            d1001 = self._latest_event(EVENT_D1001)
            if not d1001 or d1001.state != "accepted":
                raise UserError(_("D-1001 must be accepted before sending D-1011."))
        if EVENT_D1198 in types:
            closing = self._latest_event(EVENT_D1199)
            if not closing or closing.state != "accepted" or not closing.nr_recibo:
                raise UserError(_("D-1199 must be accepted before sending D-1198."))
        if EVENT_D1106 in types:
            self._require_processing_receipt(
                EVENT_D1101,
                _("D-1101 processing receipt is required before sending D-1106."),
            )
        if EVENT_D1121 in types:
            self._assert_d1121_send_order()
        if EVENT_D1199 in types:
            self._assert_d1199_send_order()

    def _next_events(self, event_types):
        self.ensure_one()
        for event_type in event_types:
            events = self.event_ids.filtered(
                lambda ev, current=event_type: ev.event_type == current
                and ev.xml_content
                and ev.state == "generated"
            )
            if events:
                return events[:1]
        return self.env["l10n_br_dere.event"]

    def action_send_periodics(self):
        result = True
        for rec in self:
            action = rec._send_events(rec._next_events(PERIODIC_EVENTS))
            if isinstance(action, dict):
                result = action
        return result

    def _get_dere_certificate(self):
        self.ensure_one()
        company = self.company_id
        if not company.certificate_nfe_id and not company.certificate_ecnpj_id:
            raise UserError(
                _(
                    "Configure an A1 certificate on the company before sending "
                    "DeRE events."
                )
            )
        return company._get_br_ecertificate()

    def _send_events(self, events):
        self.ensure_one()
        if not events:
            raise UserError(_("There is no generated event to send."))
        self._assert_send_order(events.mapped("event_type"))
        certificado = self._get_dere_certificate()
        signed_events = []
        for ev in events:
            signed_xml = xml_builder.sign_event(
                ev.xml_content, certificado, ev.event_id_attr
            )
            ev._assert_valid_xml(signed_xml, signed=True)
            signed_events.append({"id": ev.event_id_attr, "xml": signed_xml})
        xml = xml_builder.build_lote(self.company_id._dere_cnpj_root(), signed_events)
        lote_errors = xsd_validator.validate_lote(xml)
        if lote_errors:
            raise UserError(
                _("DeRE batch XML failed official XSD validation:\n%s")
                % "\n".join(lote_errors[:8])
            )
        batch_vals = {
            "name": f"{self.per_apur} {', '.join(events.mapped('event_type'))}",
            "declaration_id": self.id,
            "tp_amb": self.company_id.dere_tp_amb or "2",
            "event_ids": [(6, 0, events.ids)],
            "xml_content": xml,
        }
        batch = self.env["l10n_br_dere.batch"].create(batch_vals)
        try:
            result = self.env["l10n_br_dere.receita.integra"].send_batch(
                self.company_id, xml
            )
        except (requests.Timeout, requests.ConnectionError) as exc:
            batch.write(
                {
                    "state": "unknown",
                    "response_text": str(exc),
                }
            )
            return self._unknown_transmission_action()
        return self._apply_send_result(batch, events, result)

    def action_consult_results(self):
        consulted = self.env["l10n_br_dere.batch"]
        for rec in self:
            transmitted = rec.batch_ids.filtered(lambda batch: batch.protocol)
            if rec.table_period_id:
                transmitted |= rec.table_period_id.batch_ids.filtered(
                    lambda batch: batch.protocol
                )
            if not transmitted:
                raise UserError(_("There is no sent batch with a protocol to consult."))
            batches = transmitted.filtered(lambda batch: batch.state == "sent")
            batches.action_consult()
            consulted |= batches
        if not consulted:
            # The scheduled consult job may have processed the batch already.
            return self._notify_and_reload(
                _("Nothing to consult"),
                _("Every transmitted batch was already processed."),
            )
        return True

    def _notify_and_reload(self, title, message, notification_type="info"):
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": title,
                "message": message,
                "type": notification_type,
                "next": {"type": "ir.actions.client", "tag": "soft_reload"},
            },
        }

    def action_apply_return_xml(self, xml_content):
        self.ensure_one()
        parsed = xml_builder.parse_return(xml_content)
        events = self.event_ids
        if self.table_period_id:
            events |= self.table_period_id.event_ids
        return self._apply_parsed_return(events, parsed)

    def _apply_parsed_return(self, events, parsed, protocol=None):
        target = events
        if parsed.get("tpEv"):
            target = events.filtered(lambda ev: ev.event_type == parsed["tpEv"])
        if not target:
            return False
        return self.apply_return(
            target[0],
            parsed.get("cdRetorno") or "0",
            desc_retorno=parsed.get("descRetorno"),
            nr_recibo=parsed.get("nrRecibo"),
            protocol=parsed.get("protocoloLote") or protocol,
            occurrences=parsed.get("ocorrencias"),
            payload=parsed,
        )

    def apply_return(
        self,
        event,
        cd_retorno,
        desc_retorno=None,
        nr_recibo=None,
        protocol=None,
        occurrences=None,
        payload=None,
    ):
        event.write(
            {
                "cd_retorno": cd_retorno,
                "desc_retorno": desc_retorno,
                "nr_recibo": nr_recibo,
                "protocol": protocol or event.protocol,
                "state": "accepted" if cd_retorno == "1" else "rejected",
                **event._return_payload_vals(payload),
            }
        )
        event._check_return_schema()
        if event.event_type == EVENT_D1199 and event.state == "accepted":
            event.declaration_id.state = "closed"
        if event.event_type == EVENT_D1198 and event.state == "accepted":
            event.declaration_id.state = "reopened"
        if occurrences:
            event.occurrence_ids.unlink()
            self.env["l10n_br_dere.event.occurrence"].create(
                [
                    {
                        "event_id": event.id,
                        "codigo": item.get("codigo") or "0",
                        "descricao": item.get("descricao") or "",
                        "tipo": item.get("tipo") or "1",
                        "localizacao": item.get("localizacao"),
                    }
                    for item in occurrences
                ]
            )
        event._return_parent()._apply_return_content(event, payload)
        return True

    def _reject_batch_events(self, batch, parsed):
        events = batch.event_ids.filtered(lambda ev: ev.state == "sent")
        events.with_context(dere_force_event_write=True).write(
            {
                "state": "rejected",
                "cd_retorno": "0",
                "desc_retorno": parsed.get("descResposta") or parsed.get("descRetorno"),
            }
        )
        occurrences = parsed.get("ocorrencias") or []
        if occurrences:
            events.occurrence_ids.unlink()
            self.env["l10n_br_dere.event.occurrence"].create(
                [
                    {
                        "event_id": event.id,
                        "codigo": item.get("codigo") or "0",
                        "descricao": item.get("descricao") or "",
                        "tipo": item.get("tipo") or "1",
                        "localizacao": item.get("localizacao"),
                    }
                    for event in events
                    for item in occurrences
                ]
            )

    def _apply_consult_result(self, batch, xml_content):
        self.ensure_one()
        if not xml_content or "<" not in xml_content:
            return False
        try:
            parsed = xml_builder.parse_return(xml_content)
        except etree.XMLSyntaxError:
            return False
        cd_resposta = str(parsed.get("cdResposta") or "")
        if cd_resposta == "1":
            return False
        if cd_resposta in ("4", "5", "7", "9"):
            batch.state = "error"
            self._reject_batch_events(batch, parsed)
            return False
        protocol = (
            parsed.get("protocoloLote") or parsed.get("protocolo") or batch.protocol
        )
        applied = False
        for item in parsed.get("events") or []:
            target = batch.event_ids
            if item.get("id"):
                event_id = item["id"]
                matched = target.filtered(
                    lambda ev, current=event_id: ev.event_id_attr == current
                )
                if matched:
                    target = matched
            if item.get("tpEv"):
                event_type = item["tpEv"]
                target = target.filtered(
                    lambda ev, current=event_type: ev.event_type == current
                )
            if not target:
                continue
            self.apply_return(
                target[0],
                item.get("cdRetorno") or "0",
                desc_retorno=item.get("descRetorno"),
                nr_recibo=item.get("nrRecibo"),
                protocol=item.get("protocoloLote") or protocol,
                occurrences=item.get("ocorrencias"),
                payload=item,
            )
            applied = True
        pending = batch.event_ids.filtered(lambda ev: ev.state == "sent")
        if cd_resposta in ("2", "3") or (batch.event_ids and not pending):
            batch.state = "done"
            return True
        return applied

    def _extract_protocol(self, text):
        if not text:
            return False
        stripped = text.strip()
        if re.fullmatch(PROTOCOL_RE, stripped):
            return stripped
        if stripped.startswith("{"):
            try:
                payload = json.loads(stripped)
            except json.JSONDecodeError:
                return False
            return payload.get("protocoloLote") or payload.get("protocolo") or False
        if "<" not in stripped:
            return False
        try:
            parsed = xml_builder.parse_return(text)
        except etree.XMLSyntaxError:
            return False
        return parsed.get("protocoloLote") or parsed.get("protocolo") or False
