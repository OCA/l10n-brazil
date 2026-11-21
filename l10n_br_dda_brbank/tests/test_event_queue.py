# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import timedelta
from unittest.mock import patch

from odoo import fields
from odoo.tests import tagged
from odoo.tools import mute_logger

from ..models import dda_event
from .common import EVENT_LOGGER, DdaBrbankCommon, make_debit, make_event
from .fake_dda import STATE

DEBIT_MODEL = "l10n_br_dda.debit"


@tagged("post_install", "-at_install")
class TestEventQueue(DdaBrbankCommon):
    def new_events(self, count, connection=None, start=1):
        events = [
            make_event(f"e-{n}", self.NEW, make_debit(n))
            for n in range(start, start + count)
        ]
        self.store(*events, connection=connection)
        return events

    # === handlers === #

    def test_a_new_boleto_goes_to_the_inbox_without_asking_the_bank(self):
        self.new_events(1)
        self.run_events()
        event = self.event_of("e-1")
        self.assertEqual(event.state, "done")
        self.assertFalse(event.debits_json)
        debit = self.debits_of()
        self.assertEqual(debit.digitable_line, make_debit(1).linha_digitavel)
        self.assertEqual(debit.payer_cnpj, make_debit(1).cnpj_pagador)
        self.assertEqual(debit.amount, 101.0)
        self.assertEqual(debit.beneficiary_vat, make_debit(1).beneficiario_documento)
        self.assertEqual(debit.source_ids.source_type, "api")
        self.assertEqual(debit.source_ids.external_id, "bank-1")
        self.assertFalse(STATE["calls"])

    def test_a_changed_boleto_updates_the_inbox(self):
        self.new_events(1)
        self.run_events()
        changed = make_debit(1, valor="250.00")
        self.store(make_event("e-2", self.CHANGED, changed))
        self.run_events()
        self.assertEqual(self.debits_of().amount, 250.0)
        self.assertEqual(len(self.debits_of()), 1)

    def test_paid_at_the_bank_becomes_paid_elsewhere(self):
        self.new_events(1)
        self.run_events()
        STATE["pages"] = [[make_debit(1, status="PAGO")]]
        self.store(make_event("e-2", self.PAID, make_debit(1, status="PAGO")))
        self.run_events()
        self.assertEqual(self.event_of("e-2").state, "done")
        self.assertEqual(self.debits_of().state, "paid_elsewhere")
        # It asked the listing, from the due date of the boleto.
        self.assertEqual(STATE["calls"][0][1], make_debit(1).vencimento)

    def test_paid_that_the_listing_does_not_show_is_settled_by_the_event(self):
        self.new_events(1)
        self.run_events()
        STATE["pages"] = [[]]
        self.store(make_event("e-2", self.PAID, make_debit(1, status="PAGO")))
        self.run_events()
        self.assertEqual(self.event_of("e-2").state, "done")
        self.assertEqual(self.debits_of().state, "paid_elsewhere")

    def test_paid_that_the_listing_still_shows_open_is_retried(self):
        self.new_events(1)
        self.run_events()
        STATE["pages"] = [[make_debit(1)]]
        self.store(make_event("e-2", self.PAID, make_debit(1, status="PAGO")))
        self.run_events()
        event = self.event_of("e-2")
        self.assertEqual((event.state, event.attempts), ("error", 1))
        self.assertIn("still lists", event.last_error)
        self.assertNotEqual(self.debits_of().state, "paid_elsewhere")
        # The bank settles it: the retry, once due, closes the boleto.
        STATE["pages"] = [[make_debit(1, status="PAGO")]]
        event.next_attempt_at = fields.Datetime.now() - timedelta(minutes=1)
        self.run_events()
        self.assertEqual(event.state, "done")
        self.assertEqual(self.debits_of().state, "paid_elsewhere")

    def test_dda_disabled_at_the_bank_warns_an_administrator(self):
        self.enable()
        self.store(make_event("e-1", self.DISABLED))
        self.run_events()
        self.assertEqual(self.event_of("e-1").state, "done")
        self.assertFalse(self.connection.dda_enabled)
        status = self.connection.dda_sync_status_ids
        self.assertEqual(status.state, "error")
        activity = self.connection.activity_ids
        self.assertEqual(len(activity), 1)
        self.assertIn("disabled", activity.summary)
        # The warning is not repeated by another event.
        self.store(make_event("e-2", self.DISABLED))
        self.run_events()
        self.assertEqual(len(self.connection.activity_ids), 1)

    # === the queue === #

    def test_the_cron_works_in_blocks_and_triggers_itself_while_there_is_a_queue(self):
        self.new_events(5)
        with patch.object(dda_event, "BLOCK_SIZE", 2), patch.object(
            dda_event, "BLOCKS_PER_RUN", 1
        ):
            trigger = self.run_events()
        states = self.Event.search([("connection_id", "=", self.connection.id)]).mapped(
            "state"
        )
        self.assertEqual(sorted(states), ["done", "done", "new", "new", "new"])
        trigger.assert_called_once()
        # The next runs finish the queue, and then the cron lets itself rest.
        with patch.object(dda_event, "BLOCK_SIZE", 2):
            trigger = self.run_events()
        trigger.assert_not_called()
        self.assertEqual(len(self.debits_of()), 5)

    def test_a_block_is_fair_between_connections(self):
        other = self.new_connection(name="Other")
        self.new_events(5)
        self.new_events(1, connection=other, start=10)
        with patch.object(dda_event, "BLOCK_SIZE", 2), patch.object(
            dda_event, "BLOCKS_PER_RUN", 1
        ):
            self.run_events()
        self.assertEqual(self.event_of("e-10", connection=other).state, "done")
        self.assertEqual(self.event_of("e-1").state, "done")
        self.assertEqual(self.event_of("e-2").state, "new")

    def test_a_failing_event_does_not_stop_the_queue(self):
        self.new_events(3)
        original = type(self.env[DEBIT_MODEL])._dda_upsert

        def upsert(model, vals_list, source_type, source_key):
            if vals_list and vals_list[0]["external_id"] == "bank-2":
                raise ValueError("boom")
            return original(model, vals_list, source_type, source_key)

        with patch.object(type(self.env[DEBIT_MODEL]), "_dda_upsert", upsert):
            self.run_events()
        self.assertEqual(self.event_of("e-1").state, "done")
        self.assertEqual(self.event_of("e-3").state, "done")
        failed = self.event_of("e-2")
        self.assertEqual((failed.state, failed.attempts), ("error", 1))
        self.assertIn("ValueError", failed.last_error)
        self.assertEqual(len(self.debits_of()), 2)

    def test_backoff_doubles_up_to_an_hour(self):
        self.assertEqual(
            [dda_event.backoff_minutes(n) for n in range(1, 9)],
            [1, 2, 4, 8, 16, 32, 60, 60],
        )

    def test_a_failure_waits_before_the_next_try(self):
        self.new_events(1)
        event = self.event_of("e-1")
        with patch.object(
            type(self.env[DEBIT_MODEL]), "_dda_upsert", side_effect=ValueError("x")
        ):
            self.run_events()
            self.assertEqual((event.state, event.attempts), ("error", 1))
            self.assertAlmostEqual(self.minutes_ahead(event), 1, delta=0.1)
            # Not due yet: untouched.
            self.run_events()
            self.assertEqual(event.attempts, 1)
            event.next_attempt_at = fields.Datetime.now() - timedelta(seconds=1)
            self.run_events()
            self.assertEqual(event.attempts, 2)
            self.assertAlmostEqual(self.minutes_ahead(event), 2, delta=0.1)

    def test_eight_failures_quarantine_the_event(self):
        self.new_events(1)
        event = self.event_of("e-1")
        event.attempts = dda_event.MAX_ATTEMPTS - 1
        with patch.object(
            type(self.env[DEBIT_MODEL]), "_dda_upsert", side_effect=ValueError("x")
        ), mute_logger(EVENT_LOGGER):
            self.run_events()
        self.assertEqual(
            (event.state, event.attempts, event.next_attempt_at),
            ("quarantine", dda_event.MAX_ATTEMPTS, False),
        )
        # Nobody picks it up again.
        self.run_events()
        self.assertEqual(event.attempts, dda_event.MAX_ATTEMPTS)
        self.assertFalse(self.debits_of())

    def test_a_quarantined_event_can_be_requeued(self):
        self.new_events(1)
        event = self.event_of("e-1")
        event.write({"state": "quarantine", "attempts": 8})
        with patch("odoo.addons.base.models.ir_cron.ir_cron._trigger") as trigger:
            event.action_requeue()
        trigger.assert_called_once()
        self.assertEqual((event.state, event.attempts), ("new", 0))
        self.run_events()
        self.assertEqual(event.state, "done")
        self.assertEqual(len(self.debits_of()), 1)

    def test_events_of_an_archived_connection_wait(self):
        self.new_events(1)
        self.connection.active = False
        self.run_events()
        self.assertEqual(self.event_of("e-1").state, "new")
        self.connection.active = True
        self.run_events()
        self.assertEqual(self.event_of("e-1").state, "done")

    # === purge === #

    def age(self, events, days):
        """Move the last write of the events back in time (write_date is magic)."""
        moment = fields.Datetime.now() - timedelta(days=days)
        # Pending writes would touch write_date again when they are flushed.
        self.env.flush_all()
        self.env.cr.execute(
            "UPDATE l10n_br_dda_event SET write_date = %s WHERE id IN %s",
            (moment, tuple(events.ids)),
        )
        events.invalidate_recordset(["write_date"])

    def test_purge_deletes_only_old_processed_events(self):
        self.new_events(5)
        old_done, recent_done, old_error, old_quarantine, old_new = (
            self.event_of(f"e-{n}") for n in range(1, 6)
        )
        for event, state in (
            (old_done, "done"),
            (recent_done, "done"),
            (old_error, "error"),
            (old_quarantine, "quarantine"),
        ):
            event.state = state
        self.age(old_done | old_error | old_quarantine | old_new, 45)
        self.age(recent_done, 5)
        self.assertEqual(self.Event._cron_purge_events(), 1)
        remaining = self.Event.search([("connection_id", "=", self.connection.id)])
        self.assertEqual(
            sorted(remaining.mapped("event_id")), ["e-2", "e-3", "e-4", "e-5"]
        )
