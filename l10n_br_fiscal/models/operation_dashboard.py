# Copyright (C) 2020  KMEE - www.kmee.com.br
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import json
from collections import defaultdict
from datetime import datetime, time, timedelta

import pytz

from odoo import api, fields, models
from odoo.tools.misc import formatLang

from ..constants.fiscal import (
    DOCUMENT_STATE_CANCEL,
    DOCUMENT_STATE_DRAFT,
    DOCUMENT_STATE_INVALIDATED,
    DOCUMENT_STATE_OPEN,
)

# Pending buckets are work to do and are counted whatever the date;
# period buckets are volumes and only count the documents of the period.
PENDING_BUCKETS = ("2confirm", "processing", "error")
PERIOD_BUCKETS = ("authorized", "cancelled")
PROCESSING_LATE_AFTER = timedelta(minutes=10)


class Operation(models.Model):
    _inherit = "l10n_br_fiscal.operation"

    kanban_dashboard = fields.Text(compute="_compute_kanban_dashboard")

    dashboard_active = fields.Boolean(
        string="With Activity",
        compute="_compute_kanban_dashboard",
        search="_search_dashboard_active",
    )

    color = fields.Integer(string="Color Index", default=0)

    @api.depends_context("dashboard_period", "tz", "allowed_company_ids")
    def _compute_kanban_dashboard(self):
        data = self._get_dashboard_data()
        for operation in self:
            values = data[operation._origin.id]
            operation.kanban_dashboard = json.dumps(values)
            operation.dashboard_active = values["active"]

    def _search_dashboard_active(self, operator, value):
        if operator not in ("=", "!=") or not isinstance(value, bool):
            raise NotImplementedError(f"Unsupported search: {operator} {value}")
        data = self.search([("state", "=", "approved")])._get_dashboard_data()
        active_ids = [op_id for op_id, values in data.items() if values["active"]]
        positive = (operator == "=") == value
        return [("id", "in" if positive else "not in", active_ids)]

    def _dashboard_2confirm_states(self):
        """state_edoc values counted in the dashboard 'to confirm' bucket.

        Modules extending state_edoc (e.g. l10n_br_fiscal_edi) override
        these hooks to place their own states in the right buckets.
        """
        return [DOCUMENT_STATE_DRAFT]

    def _dashboard_processing_states(self):
        """state_edoc values waiting for the tax authority answer."""
        return []

    def _dashboard_error_states(self):
        """state_edoc values that need someone to fix the document."""
        return []

    def _dashboard_authorized_states(self):
        """state_edoc values counted in the dashboard 'authorized' bucket.

        Without an EDI module, 'open' is the final good state.
        """
        return [DOCUMENT_STATE_OPEN]

    def _dashboard_cancelled_states(self):
        """state_edoc values counted in the dashboard 'cancelled' bucket."""
        return [DOCUMENT_STATE_CANCEL, DOCUMENT_STATE_INVALIDATED]

    def _dashboard_buckets(self):
        return {
            "2confirm": self._dashboard_2confirm_states(),
            "processing": self._dashboard_processing_states(),
            "error": self._dashboard_error_states(),
            "authorized": self._dashboard_authorized_states(),
            "cancelled": self._dashboard_cancelled_states(),
        }

    def _dashboard_period_start(self):
        """UTC start of the period chosen on the dashboard, today by default."""
        today = fields.Date.context_today(self)
        start = {
            "week": today - timedelta(days=6),
            "month": today.replace(day=1),
        }.get(self.env.context.get("dashboard_period"), today)
        tz = pytz.timezone(self.env.context.get("tz") or self.env.user.tz or "UTC")
        local_start = tz.localize(datetime.combine(start, time.min))
        return local_start.astimezone(pytz.utc).replace(tzinfo=None)

    def _fiscal_document_object(self):
        return self.env["l10n_br_fiscal.document"]

    def _get_dashboard_data(self):
        """Dashboard values of every operation in self, in two queries."""
        buckets = self._dashboard_buckets()
        state_bucket = {
            state: bucket for bucket, states in buckets.items() for state in states
        }
        operation_domain = [("fiscal_operation_id", "in", self._origin.ids)]
        Document = self._fiscal_document_object()
        counts = defaultdict(lambda: defaultdict(int))
        amounts = defaultdict(float)
        oldest_processing = {}

        pending_states = [s for b in PENDING_BUCKETS for s in buckets[b]]
        for operation, state, count, oldest in Document._read_group(
            operation_domain + [("state_edoc", "in", pending_states)],
            groupby=["fiscal_operation_id", "state_edoc"],
            aggregates=["__count", "write_date:min"],
        ):
            bucket = state_bucket[state]
            counts[operation.id][bucket] += count
            if bucket == "processing":
                oldest_processing[operation.id] = min(
                    oldest, oldest_processing.get(operation.id, oldest)
                )

        period_states = [s for b in PERIOD_BUCKETS for s in buckets[b]]
        for operation, state, count, amount in Document._read_group(
            operation_domain
            + [
                ("state_edoc", "in", period_states),
                ("document_date", ">=", self._dashboard_period_start()),
            ],
            groupby=["fiscal_operation_id", "state_edoc"],
            aggregates=["__count", "fiscal_amount_total:sum"],
        ):
            bucket = state_bucket[state]
            counts[operation.id][bucket] += count
            if bucket == "authorized":
                amounts[operation.id] += amount

        # write_date tells since when a document waits for the tax authority:
        # nothing else writes on it in that state.
        late_limit = fields.Datetime.now() - PROCESSING_LATE_AFTER
        currency = self.env.company.currency_id
        period_label = {
            "week": self.env._("Last 7 days"),
            "month": self.env._("This month"),
        }.get(self.env.context.get("dashboard_period"), self.env._("Today"))
        data = {}
        for op_id in self._origin.ids:
            op_counts = counts[op_id]
            data[op_id] = {
                "number_2confirm": op_counts["2confirm"],
                "number_processing": op_counts["processing"],
                "processing_late": oldest_processing.get(op_id, late_limit)
                < late_limit,
                "number_error": op_counts["error"],
                "number_authorized": op_counts["authorized"],
                "amount_authorized": formatLang(
                    self.env, amounts[op_id], currency_obj=currency
                ),
                "number_cancelled": op_counts["cancelled"],
                "period": period_label,
                "active": any(op_counts.values()),
            }
        return data

    def get_operation_dashboard_data(self):
        self.ensure_one()
        return self._get_dashboard_data()[self.id]

    def action_create_new(self):
        ctx = self._context.copy()
        model = "l10n_br_fiscal.document"
        if self.fiscal_operation_type == "out":
            ctx.update(
                {
                    "default_fiscal_operation_type": "out",
                    "default_fiscal_operation_id": self.id,
                }
            )
        elif self.fiscal_operation_type == "in":
            ctx.update(
                {
                    "default_fiscal_operation_type": "in",
                    "default_fiscal_operation_id": self.id,
                }
            )
        return {
            "name": self.env._("Create invoice/bill"),
            "type": "ir.actions.act_window",
            "view_type": "form",
            "view_mode": "form",
            "res_model": model,
            "view_id": self.env.ref("l10n_br_fiscal.document_form").id,
            "context": ctx,
        }

    def open_action(self):
        """Documents of the operation, limited to the dashboard bucket
        (``dashboard_bucket`` in the context) when one was clicked."""

        _fiscal_type_map = {
            "purchase": "in",
            "purchase_refund": "in",
            "return_in": "in",
            "sale": "out",
            "sale_refund": "out",
            "return_out": "out",
            "other": "out",
        }
        fiscal_operation_type = _fiscal_type_map[self.fiscal_type]

        action_name = self._context.get("action_name", False)

        if not action_name:
            action_name = (
                "document_out_action"
                if fiscal_operation_type == "out"
                else "document_in_action"
            )

        ctx = self._context.copy()
        ctx.pop("group_by", None)
        bucket = ctx.pop("dashboard_bucket", None)
        ctx.update(
            {
                "default_fiscal_operation_type": fiscal_operation_type,
            }
        )

        xmlid = f"l10n_br_fiscal.{action_name}"
        [action] = self.env.ref(xmlid).read()
        action["context"] = ctx
        action["domain"] = self._context.get("use_domain", [])
        action["domain"] += [("fiscal_operation_id", "=", self.id)]
        if bucket:
            action["domain"] += [
                ("state_edoc", "in", self._dashboard_buckets()[bucket])
            ]
        if bucket in PERIOD_BUCKETS:
            action["domain"] += [
                (
                    "document_date",
                    ">=",
                    fields.Datetime.to_string(self._dashboard_period_start()),
                )
            ]
        return action
