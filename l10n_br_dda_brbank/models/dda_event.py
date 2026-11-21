# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import json
import logging
import threading
from datetime import datetime, timedelta

import psycopg2
from brbank.dda import TipoEventoDda

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import config, mute_logger

from odoo.addons.l10n_br_dda.utils import normalize_digitable_line

from ..utils import debit_to_vals, same_payer, source_key

_logger = logging.getLogger(__name__)

# Events committed together; the cron triggers itself again while there is a queue.
BLOCK_SIZE = 20
BLOCKS_PER_RUN = 5
# After this many failures the event stops being retried (quarantine).
MAX_ATTEMPTS = 8
BACKOFF_CAP_MINUTES = 60
PAYLOAD_LIMIT = 8000
# Processed events are kept this many days (system parameter below), then purged.
PURGE_BLOCK_SIZE = 500
RETENTION_PARAM = "l10n_br_dda_brbank.event_retention_days"
DEFAULT_RETENTION_DAYS = 30
CRON_XMLID = "l10n_br_dda_brbank.ir_cron_dda_process_events"
EVENT_TYPES = [(kind.value, kind.value) for kind in TipoEventoDda]
# Notifications of the state of the DDA at the bank, not of a boleto.
STATE_EVENT_TYPES = (TipoEventoDda.DDA_ATIVADO, TipoEventoDda.DDA_DESATIVADO)


def backoff_minutes(attempts):
    """Wait before the next try after `attempts` failures: 1, 2, 4... 60."""
    return min(2 ** max(attempts - 1, 0), BACKOFF_CAP_MINUTES)


class DdaEvent(models.Model):
    """A DDA event of the bank, kept until a cron processes it."""

    _name = "l10n_br_dda.event"
    _description = "DDA Bank Event"
    _order = "id desc"
    _rec_name = "event_id"

    connection_id = fields.Many2one(
        comodel_name="l10n_br_bank_connection.connection",
        required=True,
        ondelete="cascade",
        index=True,
        readonly=True,
    )
    event_id = fields.Char(required=True, index=True, readonly=True)
    event_type = fields.Selection(selection=EVENT_TYPES, required=True, readonly=True)
    occurred_at = fields.Datetime(readonly=True)
    state = fields.Selection(
        selection=[
            ("new", "To Process"),
            ("done", "Processed"),
            ("error", "Retrying"),
            ("quarantine", "Quarantine"),
        ],
        default="new",
        required=True,
        readonly=True,
        index=True,
    )
    attempts = fields.Integer(readonly=True)
    next_attempt_at = fields.Datetime(readonly=True)
    last_error = fields.Char(readonly=True)
    payload = fields.Text(
        readonly=True,
        groups="base.group_no_one",
        help="Event as received, masked by the library.",
    )
    debits_json = fields.Text(
        readonly=True,
        groups="base.group_no_one",
        help="Boletos of the event as values of the DDA inbox, kept until the "
        "event is processed.",
    )

    _sql_constraints = [
        (
            "connection_event_unique",
            "unique(connection_id, event_id)",
            "This DDA event was already received.",
        )
    ]

    # === STORE === #

    @api.model
    def _dda_store(self, connection, events):
        """Persist the events of the library, skipping the ones already received."""
        created = self.browse()
        for event in events:
            if event.cnpj_pagador and not same_payer(
                connection.cnpj, event.cnpj_pagador
            ):
                _logger.info(
                    "DDA connection %s: event of another payer CNPJ ignored",
                    connection.id,
                )
                continue
            event_id = self._dda_event_key(connection, event)
            if not event_id:
                continue
            debits = [
                debit_to_vals(debit)
                for debit in event.debitos
                if same_payer(connection.cnpj, debit.cnpj_pagador)
            ]
            moment = event.ocorrido_em
            if moment and moment.tzinfo:
                moment = moment.astimezone(tz=None).replace(tzinfo=None)
            values = {
                "connection_id": connection.id,
                "event_id": event_id,
                "event_type": event.tipo.value,
                "occurred_at": moment or False,
                "debits_json": json.dumps(debits),
                "payload": json.dumps(
                    event.resposta_bruta, default=str, sort_keys=True
                )[:PAYLOAD_LIMIT],
            }
            try:
                with mute_logger("odoo.sql_db"), self.env.cr.savepoint():
                    created |= self.create(values)
            except psycopg2.IntegrityError:
                # The same event arrived twice at the same time.
                continue
        return created

    @api.model
    def _dda_event_key(self, connection, event):
        """Key to store `event` under, or False when it is a resend to skip."""
        key = event.id_evento
        same = self.search(
            [("connection_id", "=", connection.id), ("event_id", "=like", key + "%")],
            order="id desc",
        ).filtered(lambda ev: ev.event_id == key or ev.event_id.startswith(key + "#"))
        if not same:
            return key
        if event.tipo not in STATE_EVENT_TYPES:
            return False
        last_state = self.search(
            [
                ("connection_id", "=", connection.id),
                ("event_type", "in", [t.value for t in STATE_EVENT_TYPES]),
            ],
            order="id desc",
            limit=1,
        )
        if last_state in same:
            return False
        return "%s#%d" % (key, len(same))

    # === QUEUE === #

    @api.model
    def _dda_can_commit(self):
        """False while tests run: their one transaction cannot be committed."""
        return not (
            self.env.registry.in_test_mode()
            or config["test_enable"]
            or getattr(threading.current_thread(), "testing", False)
            or self.env.context.get("dda_no_commit")
        )

    @api.model
    def _dda_commit(self):
        """Commit the work done so far; the one commit of this module."""
        if self._dda_can_commit():
            # Per block of events: a later failure must not redo what is done.
            self.env.cr.commit()  # pylint: disable=invalid-commit

    @api.model
    def _dda_due_domain(self):
        return [
            ("state", "in", ("new", "error")),
            "|",
            ("next_attempt_at", "=", False),
            ("next_attempt_at", "<=", fields.Datetime.now()),
            ("connection_id.active", "=", True),
        ]

    @api.model
    def _dda_next_block(self):
        """Next events to handle: oldest first, round robin between connections."""
        domain = self._dda_due_domain()
        queues = []
        for group in self.read_group(domain, ["connection_id"], ["connection_id"]):
            events = self.search(
                domain + [("connection_id", "=", group["connection_id"][0])],
                order="id",
                limit=BLOCK_SIZE,
            )
            events = events.sorted(
                key=lambda e: (e.next_attempt_at or datetime.min, e.id)
            )
            queues.append(list(events))
        queues.sort(key=lambda queue: queue[0].id)
        block = []
        while len(block) < BLOCK_SIZE and any(queues):
            for queue in queues:
                if queue and len(block) < BLOCK_SIZE:
                    block.append(queue.pop(0))
        return self.browse([event.id for event in block])

    @api.model
    def _cron_process_events(self):
        events = self.sudo()
        for _block in range(BLOCKS_PER_RUN):
            block = events._dda_next_block()
            if not block:
                return
            for event in block:
                event._dda_process_one()
            events._dda_commit()
        if events.search_count(events._dda_due_domain()):
            self.env.ref(CRON_XMLID).sudo()._trigger()

    @api.model
    def _dda_retention_days(self):
        value = self.env["ir.config_parameter"].sudo().get_param(RETENTION_PARAM)
        if not value:
            return DEFAULT_RETENTION_DAYS
        try:
            return max(int(value), 0)
        except (TypeError, ValueError):
            return DEFAULT_RETENTION_DAYS

    @api.model
    def _cron_purge_events(self):
        """Delete the processed events older than the retention period."""
        events = self.sudo()
        cutoff = fields.Datetime.now() - timedelta(days=events._dda_retention_days())
        total = 0
        while True:
            block = events.search(
                [("state", "=", "done"), ("write_date", "<", cutoff)],
                limit=PURGE_BLOCK_SIZE,
                order="id",
            )
            if not block:
                break
            total += len(block)
            block.unlink()
            events._dda_commit()
        if total:
            _logger.info("DDA events: %s processed events purged", total)
        return total

    def _dda_process_one(self):
        self.ensure_one()
        try:
            with self.env.cr.savepoint():
                self._dda_dispatch()
        except Exception as error:  # pylint: disable=broad-except
            # Whatever one event does, the queue must go on.
            self._dda_fail(error)
            return
        self.write(
            {
                "state": "done",
                "last_error": False,
                "next_attempt_at": False,
                # The boletos live in the inbox now.
                "debits_json": False,
            }
        )

    def _dda_fail(self, error):
        self.ensure_one()
        attempts = self.attempts + 1
        values = {
            "attempts": attempts,
            "last_error": f"{type(error).__name__}: {error}"[:500],
        }
        if attempts >= MAX_ATTEMPTS:
            values.update(state="quarantine", next_attempt_at=False)
            _logger.warning(
                "DDA event %s of connection %s went to quarantine",
                self.id,
                self.connection_id.id,
            )
        else:
            values.update(
                state="error",
                next_attempt_at=fields.Datetime.now()
                + timedelta(minutes=backoff_minutes(attempts)),
            )
        self.write(values)

    # === HANDLERS === #

    def _dda_dispatch(self):
        self.ensure_one()
        connection = self.connection_id
        key = source_key(connection)
        debits = json.loads(self.debits_json or "[]")
        Debit = self.env["l10n_br_dda.debit"]
        kind = self.event_type
        if kind in (TipoEventoDda.DEBITO_NOVO, TipoEventoDda.DEBITO_ALTERADO):
            # The event already carries the boleto: no query to the bank.
            Debit._dda_upsert(debits, "api", key)
        elif kind == TipoEventoDda.DEBITO_PAGO:
            Debit._dda_upsert(self._dda_paid_vals(connection, debits), "api", key)
        elif kind == TipoEventoDda.DDA_DESATIVADO:
            connection._dda_bank_disabled()
        elif kind == TipoEventoDda.DDA_ATIVADO:
            connection._dda_bank_enabled()

    def _dda_paid_vals(self, connection, debits):
        """Vals of the boletos the bank says are paid, read back from the listing."""
        found = connection._dda_lookup(debits) if debits else {}
        result = []
        for debit in debits:
            current = found.get(normalize_digitable_line(debit["digitable_line"]))
            if current is None:
                # No staleness check: the event is the only source of this one.
                result.append(dict(debit, status="PAGO", updated_at=None))
            elif current["status"] != "PAGO":
                raise UserError(_("The bank still lists the boleto as open."))
            else:
                result.append(current)
        return result

    def action_requeue(self):
        """Give a quarantined or failed event a fresh start."""
        events = self.filtered(lambda e: e.state in ("error", "quarantine"))
        events.sudo().write({"state": "new", "attempts": 0, "next_attempt_at": False})
        if events:
            self.env.ref(CRON_XMLID).sudo()._trigger()
        return True
