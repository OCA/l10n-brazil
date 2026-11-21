# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging
from datetime import timedelta

from brbank.dda import CapacidadeDda

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from ..utils import debit_to_vals, same_payer, source_key
from .dda_event import CRON_XMLID

_logger = logging.getLogger(__name__)

INCREMENTAL_CRON_XMLID = "l10n_br_dda_brbank.ir_cron_dda_incremental"
ADMIN_GROUP = "l10n_br_bank_connection.group_bank_connection_admin"
# The listing filters by due date, so the incremental pull goes back a week.
INCREMENTAL_LOOKBACK_DAYS = 7
# Pages read looking for a boleto the bank says was paid.
LOOKUP_PAGES = 20
# Guard against a bank whose cursor never ends.
MAX_PAGES = 1000


class BankConnection(models.Model):
    _name = "l10n_br_bank_connection.connection"
    _inherit = ["l10n_br_bank_connection.connection", "mail.activity.mixin"]

    dda_enabled = fields.Boolean(
        string="DDA Enabled",
        readonly=True,
        copy=False,
        tracking=True,
        help="The connection captures the boletos registered against its CNPJ.",
    )
    dda_available = fields.Boolean(compute="_compute_dda_available")
    dda_last_cursor = fields.Char(
        readonly=True,
        copy=False,
        help="Where an interrupted pull resumes: mode, due date filter and "
        "cursor of the page.",
    )
    dda_last_incremental = fields.Datetime(
        string="Last Incremental Pull", readonly=True
    )
    dda_last_full = fields.Datetime(string="Last Full Reconciliation", readonly=True)
    dda_event_ids = fields.One2many(
        comodel_name="l10n_br_dda.event",
        inverse_name="connection_id",
        string="DDA Events",
        readonly=True,
    )
    dda_pending_events = fields.Integer(compute="_compute_dda_pending_events")
    dda_sync_status_ids = fields.One2many(
        comodel_name="l10n_br_bank_connection.sync_status",
        inverse_name="connection_id",
        domain=[("domain", "=", "dda")],
        string="DDA Synchronization",
        readonly=True,
    )

    # === COMPUTE METHODS === #

    @api.depends("adapter")
    def _compute_dda_available(self):
        for connection in self:
            connection.dda_available = connection._dda_supports()

    def _compute_dda_pending_events(self):
        counts = {
            group["connection_id"][0]: group["connection_id_count"]
            for group in self.env["l10n_br_dda.event"]
            .sudo()
            .read_group(
                [
                    ("connection_id", "in", self.ids),
                    ("state", "in", ("new", "error", "quarantine")),
                ],
                ["connection_id"],
                ["connection_id"],
            )
        }
        for connection in self:
            connection.dda_pending_events = counts.get(connection.id, 0)

    # === ADAPTER === #

    def _dda_supports(self, capability=None):
        """Whether the adapter takes part in DDA (and has `capability`)."""
        self.ensure_one()
        adapter_class = self._l10n_br_bank_adapter_class()
        if not self._l10n_br_bank_dda_capable(adapter_class):
            return False
        if capability is None:
            return True
        return getattr(CapacidadeDda, capability) in adapter_class.capacidades_dda

    def _dda_require(self, capability):
        if not self._dda_supports(capability):
            raise UserError(
                _("The bank adapter of %s does not support this DDA operation.")
                % self.name
            )

    # === WEBHOOK === #

    def _l10n_br_bank_handle_webhook(self, body, headers):
        """DDA side of the webhook: store the events, process them in a cron."""
        counts = super()._l10n_br_bank_handle_webhook(body, headers)
        if not self._dda_supports("WEBHOOK"):
            return counts
        # Parsing is local work: it must not flip the state of the connection.
        events = self._l10n_br_bank_run(
            lambda adapter: adapter.parse_webhook_dda(body, headers), record=False
        )
        created = self.env["l10n_br_dda.event"].sudo()._dda_store(self, events)
        if created:
            self.env.ref(CRON_XMLID).sudo()._trigger()
        counts["dda"] = counts.get("dda", 0) + len(events)
        counts["dda_new"] = counts.get("dda_new", 0) + len(created)
        return counts

    # === TEST === #

    def _l10n_br_bank_test_connection(self):
        lines = super()._l10n_br_bank_test_connection()
        if self.dda_enabled and self._dda_supports("RESUMO"):
            cnpj = self.cnpj
            summary = self._l10n_br_bank_run(
                lambda adapter: adapter.resumo_debitos(cnpj)
            )
            lines.append(
                _(
                    "DDA: %(count)s boletos, total %(total)s.",
                    count=summary.quantidade,
                    total="%.2f" % summary.valor_total,
                )
            )
        return lines

    # === ACTIONS === #

    def _dda_notification(self, message, kind="success"):
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": self.name,
                "message": message,
                "type": kind,
                "next": {"type": "ir.actions.act_window_close"},
            },
        }

    def action_enable_dda(self):
        """Turn DDA on at the bank and start capturing the boletos."""
        self.ensure_one()
        self.check_access_rights("write")
        self._dda_require("ATIVACAO")
        cnpj = self.cnpj
        self._l10n_br_bank_run(lambda adapter: adapter.ativar_dda(cnpj))
        self.write({"dda_enabled": True})
        self._l10n_br_bank_sync_report(
            "dda", "warning", _("DDA enabled, waiting for the first synchronization.")
        )
        # The first pull is a full one (no full reconciliation yet).
        self.env.ref(INCREMENTAL_CRON_XMLID).sudo()._trigger()
        return self._dda_notification(_("DDA enabled."))

    def action_disable_dda(self):
        """Turn DDA off at the bank; the boletos already captured stay."""
        self.ensure_one()
        self.check_access_rights("write")
        self._dda_require("ATIVACAO")
        cnpj = self.cnpj
        self._l10n_br_bank_run(lambda adapter: adapter.desativar_dda(cnpj))
        self.write({"dda_enabled": False, "dda_last_cursor": False})
        self._l10n_br_bank_sync_report("dda", "warning", _("DDA disabled."))
        return self._dda_notification(_("DDA disabled."))

    def action_dda_sync_now(self):
        """Pull the listing now (a full one while there was none)."""
        self.ensure_one()
        self.check_access_rights("write")
        if not self.dda_enabled:
            raise UserError(_("Enable DDA on this connection first."))
        total = self._dda_pull(full=not self.dda_last_full)
        return self._dda_notification(_("%s boletos synchronized.", total))

    # === BANK SIDE CHANGES === #

    def _dda_bank_enabled(self):
        """The bank says DDA was turned on."""
        self.ensure_one()
        if not self.dda_enabled:
            self.sudo().write({"dda_enabled": True})
        self._l10n_br_bank_sync_report("dda", True, _("DDA enabled at the bank."))

    def _dda_bank_disabled(self):
        """The bank says DDA was turned off: stop pulling and warn an admin."""
        self.ensure_one()
        message = _("DDA was disabled at the bank.")
        self.sudo().write({"dda_enabled": False, "dda_last_cursor": False})
        self._l10n_br_bank_sync_report("dda", False, message)
        self._dda_schedule_admin_activity(
            message,
            _("No new boleto arrives until DDA is enabled again on the connection."),
        )

    def _dda_schedule_admin_activity(self, summary, note):
        self.ensure_one()
        if self.activity_ids.filtered(lambda activity: activity.summary == summary):
            return
        group = self.env.ref(ADMIN_GROUP).sudo()
        admins = group.users.filtered(lambda user: user.active and not user.share)
        user = self.create_uid if self.create_uid in admins else admins[:1]
        if not user:
            _logger.warning("DDA connection %s: no administrator to warn", self.id)
            return
        self.activity_schedule(
            "mail.mail_activity_data_todo",
            summary=summary,
            note=note,
            user_id=user.id,
        )

    # === LOOKUP === #

    def _dda_lookup(self, debits):
        """Find boletos (vals of the event) in the listing of the bank."""
        self.ensure_one()
        wanted = {debit["digitable_line"] for debit in debits}
        due_dates = [debit.get("date_due") for debit in debits]
        since = (
            fields.Date.to_date(min(due_dates))
            if all(due_dates) and due_dates
            else None
        )
        cnpj = self.cnpj

        async def look(adapter):
            found = {}
            cursor = None
            for _page in range(LOOKUP_PAGES):
                page = await adapter.listar_debitos(cnpj, desde=since, cursor=cursor)
                for item in page.itens:
                    if item.linha_digitavel in wanted:
                        found[item.linha_digitavel] = debit_to_vals(item)
                following = page.cursor_proximo
                if len(found) == len(wanted) or not following or following == cursor:
                    break
                cursor = following
            return found

        return self._l10n_br_bank_run(look)

    # === PULL === #

    @api.model
    def _dda_pack_cursor(self, mode, since, cursor):
        return "|".join((mode, since.isoformat() if since else "", cursor))

    def _dda_resume_cursor(self, mode, since):
        """Cursor of an interrupted pull of the same kind and filter, or None."""
        self.ensure_one()
        parts = (self.dda_last_cursor or "").split("|")
        if (
            len(parts) == 3
            and parts[0] == mode
            and parts[1] == (since.isoformat() if since else "")
            and parts[2]
        ):
            return parts[2]
        return None

    def _dda_since(self):
        """Due date filter of the incremental pull."""
        self.ensure_one()
        last = self.dda_last_incremental or self.dda_last_full
        if not last:
            return None
        return last.date() - timedelta(days=INCREMENTAL_LOOKBACK_DAYS)

    def _dda_pull(self, full=False):
        """Read the listing of the bank into the DDA inbox, committing page by page."""
        self.ensure_one()
        self._dda_require("CONSULTA")
        mode = "full" if full else "inc"
        since = None if full else self._dda_since()
        cursor = self._dda_resume_cursor(mode, since)
        cnpj = self.cnpj
        started = fields.Datetime.now()
        key = source_key(self)
        debit_model = self.env["l10n_br_dda.debit"]
        event_model = self.env["l10n_br_dda.event"]
        total = 0
        for _page in range(MAX_PAGES):
            page = self._l10n_br_bank_run(
                lambda adapter, c=cursor: adapter.listar_debitos(
                    cnpj, desde=since, cursor=c
                )
            )
            vals_list = [
                debit_to_vals(debit)
                for debit in page.itens
                if same_payer(cnpj, debit.cnpj_pagador)
            ]
            with self.env.cr.savepoint():
                debit_model._dda_upsert(vals_list, "api", key)
            total += len(vals_list)
            following = page.cursor_proximo
            if following == cursor:
                following = None
            self.sudo().write(
                {
                    "dda_last_cursor": self._dda_pack_cursor(mode, since, following)
                    if following
                    else False
                }
            )
            event_model._dda_commit()
            if not following:
                break
            cursor = following
        done = {"dda_last_incremental": started}
        if full:
            done["dda_last_full"] = started
        self.sudo().write(done)
        self._l10n_br_bank_sync_report(
            "dda",
            True,
            _("%(count)s boletos listed (%(mode)s).")
            % {"count": total, "mode": _("full") if full else _("incremental")},
        )
        event_model._dda_commit()
        return total

    @api.model
    def _dda_connections(self):
        return self.sudo().search(
            [
                ("dda_enabled", "=", True),
                ("active", "=", True),
                ("state", "in", ("connected", "error")),
            ]
        )

    @api.model
    def _dda_run_cron(self, full):
        event_model = self.env["l10n_br_dda.event"]
        for connection in self._dda_connections():
            try:
                connection._dda_pull(full=full or not connection.dda_last_full)
            except Exception as error:  # pylint: disable=broad-except
                # One connection failing must not stop the others.
                _logger.warning(
                    "DDA connection %s: pull failed (%s)",
                    connection.id,
                    type(error).__name__,
                )
                connection._l10n_br_bank_sync_report(
                    "dda", False, f"{type(error).__name__}: {error}"[:200]
                )
            event_model._dda_commit()

    @api.model
    def _cron_dda_incremental(self):
        self._dda_run_cron(full=False)

    @api.model
    def _cron_dda_reconcile(self):
        self._dda_run_cron(full=True)
