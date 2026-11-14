# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import json
import logging
from datetime import timezone

import psycopg2
from brbank import StatusCanonico
from brbank.erros import ErroBrbank, Indisponivel

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import mute_logger

from .payment_provider import BRBANK

_logger = logging.getLogger(__name__)

MAX_ATTEMPTS = 10
RAW_LIMIT = 4000


class BrbankEvent(models.Model):
    """A webhook event of a bank, kept until a cron reads the title back."""

    _name = "l10n_br.brbank.event"
    _description = "Bank Webhook Event"
    _order = "id desc"
    _rec_name = "reference"

    connection_id = fields.Many2one(
        comodel_name="l10n_br_bank_connection.connection",
        required=True,
        ondelete="cascade",
        index=True,
        readonly=True,
    )
    provider_id = fields.Many2one(
        comodel_name="payment.provider",
        string="Provider",
        ondelete="set null",
        readonly=True,
        help="Provider the event was received for, when known.",
    )
    bank = fields.Char(required=True, readonly=True)
    reference = fields.Char(required=True, index=True, readonly=True)
    event_type = fields.Selection(
        selection=[(status.value, status.value) for status in StatusCanonico],
        required=True,
        readonly=True,
    )
    occurred_at = fields.Datetime(readonly=True)
    amount_paid = fields.Float(digits=(16, 2), readonly=True)
    raw_payload = fields.Text(
        readonly=True,
        groups="base.group_no_one",
        help="Event as received, masked by the library.",
    )
    state = fields.Selection(
        selection=[
            ("new", "To Process"),
            ("done", "Processed"),
            ("ignored", "Ignored"),
            ("error", "Error"),
        ],
        default="new",
        required=True,
        readonly=True,
        index=True,
    )
    attempts = fields.Integer(readonly=True)
    result_message = fields.Char(string="Result", readonly=True)
    transaction_id = fields.Many2one(
        comodel_name="payment.transaction", readonly=True, ondelete="set null"
    )

    _sql_constraints = [
        (
            "connection_event_unique",
            "unique(connection_id, bank, reference, event_type)",
            "This bank event was already received.",
        )
    ]

    @api.model
    def _brbank_store(self, connection, events):
        """Persist the canonical events, skipping the ones already received."""
        created = self.browse()
        for event in events:
            key = [
                ("connection_id", "=", connection.id),
                ("bank", "=", event.banco),
                ("reference", "=", event.referencia),
                ("event_type", "=", event.tipo.value),
            ]
            if self.search_count(key):
                continue
            values = {
                "connection_id": connection.id,
                "bank": event.banco,
                "reference": event.referencia,
                "event_type": event.tipo.value,
                "occurred_at": self._brbank_naive_utc(event.ocorrido_em),
                "amount_paid": float(event.valor_pago or 0),
                "raw_payload": json.dumps(
                    event.resposta_bruta, default=str, sort_keys=True
                )[:RAW_LIMIT],
            }
            try:
                with mute_logger("odoo.sql_db"), self.env.cr.savepoint():
                    created |= self.create(values)
            except psycopg2.IntegrityError:
                # The same event arrived twice at the same time.
                continue
        return created

    @api.model
    def _brbank_naive_utc(self, moment):
        if not moment:
            return False
        if moment.tzinfo:
            moment = moment.astimezone(timezone.utc)
        return moment.replace(tzinfo=None)

    def _brbank_find_transaction(self):
        self.ensure_one()
        return self.env["payment.transaction"].search(
            [
                ("provider_id.brbank_connection_id", "=", self.connection_id.id),
                ("provider_code", "=", BRBANK),
                "|",
                "|",
                ("provider_reference", "=", self.reference),
                ("txid", "=", self.reference),
                ("our_number", "=", self.reference),
            ],
            limit=1,
        )

    def _brbank_process(self):
        """Read the title back from the bank and apply what the bank says."""
        self.ensure_one()
        transaction = self._brbank_find_transaction()
        if not transaction:
            self.write(
                {"state": "ignored", "result_message": _("No transaction found.")}
            )
            return
        try:
            with self.env.cr.savepoint():
                transaction._brbank_sync_from_bank()
        except Indisponivel as error:
            attempts = self.attempts + 1
            self.write(
                {
                    "attempts": attempts,
                    "state": "error" if attempts >= MAX_ATTEMPTS else "new",
                    "result_message": str(error),
                    "transaction_id": transaction.id,
                }
            )
            return
        except (ErroBrbank, UserError) as error:
            self.write(
                {
                    "state": "error",
                    "result_message": str(error),
                    "transaction_id": transaction.id,
                }
            )
            return
        self.write(
            {
                "state": "done",
                "transaction_id": transaction.id,
                "result_message": _(
                    "Bank status after the query: %s", transaction.brbank_bank_status
                ),
            }
        )

    @api.model
    def _cron_process_events(self, limit=100):
        events = self.search([("state", "=", "new")], order="id", limit=limit)
        for event in events:
            event._brbank_process()

    def action_process(self):
        for event in self.filtered(lambda e: e.state in ("new", "error")):
            event.state = "new"
            event._brbank_process()
