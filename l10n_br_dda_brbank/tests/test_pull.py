# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import timedelta
from unittest.mock import patch

from brbank.erros import Indisponivel

from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tools import mute_logger

from ..models import bank_connection
from ..utils import source_key
from .common import CONNECTION_LOGGER, CRON_TRIGGER, DdaBrbankCommon, make_debit
from .fake_dda import STATE


@tagged("post_install", "-at_install")
class TestPull(DdaBrbankCommon):
    def pages(self, *sizes):
        number = 0
        pages = []
        for size in sizes:
            page = []
            for _item in range(size):
                number += 1
                page.append(make_debit(number))
            pages.append(page)
        STATE["pages"] = pages
        return number

    # === full pull === #

    def test_a_full_pull_reads_every_page(self):
        total = self.pages(2, 2, 1)
        self.assertEqual(self.connection._dda_pull(full=True), total)
        self.assertEqual(len(self.debits_of()), 5)
        self.assertEqual(
            [(cnpj, since, cursor) for cnpj, since, cursor in STATE["calls"]],
            [(self.connection.cnpj, None, cursor) for cursor in (None, "1", "2")],
        )
        self.assertTrue(self.connection.dda_last_full)
        self.assertTrue(self.connection.dda_last_incremental)
        self.assertFalse(self.connection.dda_last_cursor)
        status = self.connection.dda_sync_status_ids
        self.assertEqual(status.state, "ok")
        self.assertIn("5", status.message)

    def test_repeating_the_pull_does_not_duplicate(self):
        self.pages(2, 1)
        self.connection._dda_pull(full=True)
        self.connection._dda_pull(full=True)
        self.assertEqual(len(self.debits_of()), 3)
        sources = self.env["l10n_br_dda.debit.source"].search(
            [("source_key", "=", source_key(self.connection))]
        )
        self.assertEqual(len(sources), 3)

    def test_a_paid_boleto_in_the_listing_becomes_paid_elsewhere(self):
        STATE["pages"] = [[make_debit(1)]]
        self.connection._dda_pull(full=True)
        STATE["pages"] = [[make_debit(1, status="PAGO")]]
        self.connection._dda_pull(full=True)
        self.assertEqual(self.debits_of().state, "paid_elsewhere")

    def test_a_boleto_of_another_payer_is_not_taken(self):
        STATE["pages"] = [[make_debit(1, cnpj_pagador="98585666000153")]]
        self.assertEqual(self.connection._dda_pull(full=True), 0)
        self.assertFalse(self.debits_of())

    # === incremental pull === #

    def test_the_incremental_pull_goes_back_before_the_last_pull(self):
        self.pages(1)
        self.connection._dda_pull(full=True)
        STATE["calls"].clear()
        self.connection._dda_pull(full=False)
        since = STATE["calls"][0][1]
        expected = self.connection.dda_last_full.date() - timedelta(
            days=bank_connection.INCREMENTAL_LOOKBACK_DAYS
        )
        # `dda_last_incremental` moved on; the filter came from the full one.
        self.assertEqual(since, expected)

    def test_an_interrupted_pull_resumes_at_its_cursor(self):
        self.pages(1, 1, 1)
        self.connection.dda_last_cursor = "full||1"
        self.connection._dda_pull(full=True)
        self.assertEqual([call[2] for call in STATE["calls"]], ["1", "2"])
        self.assertEqual(len(self.debits_of()), 2)

    def test_a_cursor_that_does_not_advance_ends_the_pull(self):
        STATE["pages"] = [[make_debit(1)], [make_debit(2)]]
        STATE["stuck"] = "1"
        self.connection._dda_pull(full=True)
        self.assertEqual([call[2] for call in STATE["calls"]], [None, "1"])
        self.assertEqual(len(self.debits_of()), 2)

    # === crons === #

    def test_the_crons_pull_only_connections_with_dda_on(self):
        other = self.new_connection(name="Off")
        self.pages(2)
        self.enable()
        self.env["l10n_br_bank_connection.connection"]._cron_dda_incremental()
        self.assertEqual(len(self.debits_of()), 2)
        self.assertFalse(self.debits_of(other))
        self.assertEqual(len(STATE["calls"]), 1)

    def test_the_first_pull_is_a_full_one_then_the_cron_is_incremental(self):
        self.pages(1)
        self.enable()
        model = self.env["l10n_br_bank_connection.connection"]
        model._cron_dda_incremental()
        self.assertEqual(STATE["calls"][0][1], None)
        self.assertTrue(self.connection.dda_last_full)
        model._cron_dda_incremental()
        self.assertIsNotNone(STATE["calls"][1][1])
        model._cron_dda_reconcile()
        self.assertIsNone(STATE["calls"][2][1])

    def test_a_failing_connection_does_not_stop_the_others(self):
        other = self.enable(self.new_connection(name="Second"))
        self.enable()
        self.pages(1, 1)
        model = self.env["l10n_br_bank_connection.connection"]

        original = type(self.connection)._dda_pull

        def pull(connection, full=False):
            if connection == self.connection:
                raise Indisponivel("bank down")
            return original(connection, full=full)

        with (
            patch.object(type(self.connection), "_dda_pull", pull),
            mute_logger(CONNECTION_LOGGER),
        ):
            model._cron_dda_reconcile()
        status = self.connection.dda_sync_status_ids
        self.assertEqual(status.state, "error")
        self.assertIn("Indisponivel", status.message)
        self.assertEqual(len(self.debits_of(other)), 2)

    def test_a_listing_error_is_reported_and_the_next_run_resumes(self):
        self.enable()
        self.pages(1, 1)
        model = self.env["l10n_br_bank_connection.connection"]
        original = type(self.connection)._l10n_br_bank_run
        calls = []

        def run(connection, operation, callbacks=None, record=True):
            calls.append(1)
            if len(calls) == 2:
                raise Indisponivel("bank down")
            return original(connection, operation, callbacks, record)

        with (
            patch.object(type(self.connection), "_l10n_br_bank_run", run),
            mute_logger(CONNECTION_LOGGER),
        ):
            model._cron_dda_reconcile()
        self.assertEqual(self.connection.dda_sync_status_ids.state, "error")
        self.assertEqual(self.connection.dda_last_cursor, "full||1")
        self.assertEqual(len(self.debits_of()), 1)
        STATE["calls"].clear()
        model._cron_dda_reconcile()
        self.assertEqual([call[2] for call in STATE["calls"]], ["1"])
        self.assertEqual(len(self.debits_of()), 2)
        self.assertEqual(self.connection.dda_sync_status_ids.state, "ok")

    # === actions === #

    def test_enabling_dda_calls_the_bank_and_triggers_the_first_pull(self):
        with patch(CRON_TRIGGER) as trigger:
            action = self.connection.action_enable_dda()
        self.assertEqual(STATE["activation"], ["on"])
        self.assertTrue(self.connection.dda_enabled)
        self.assertEqual(self.connection.dda_sync_status_ids.state, "warning")
        trigger.assert_called_once()
        self.assertEqual(action["tag"], "display_notification")

    def test_disabling_dda_calls_the_bank_and_stops_the_pull(self):
        self.enable()
        self.connection.dda_last_cursor = "full||3"
        self.connection.action_disable_dda()
        self.assertEqual(STATE["activation"], ["off"])
        self.assertFalse(self.connection.dda_enabled)
        self.assertFalse(self.connection.dda_last_cursor)
        self.pages(1)
        self.env["l10n_br_bank_connection.connection"]._cron_dda_incremental()
        self.assertFalse(STATE["calls"])

    def test_synchronize_now_needs_dda_on(self):
        with self.assertRaises(UserError):
            self.connection.action_dda_sync_now()
        self.enable()
        self.pages(2)
        self.connection.action_dda_sync_now()
        self.assertEqual(len(self.debits_of()), 2)

    # === source status === #

    def sources(self):
        return {
            source["key"]: source
            for source in self.Debit._dda_source_status()
            if source["key"].startswith("connection:")
        }

    def test_the_connections_with_dda_show_up_as_sources(self):
        self.assertFalse(self.sources(), "DDA off: not a source")
        self.enable()
        key = source_key(self.connection)
        source = self.sources()[key]
        self.assertEqual(source["state"], "warning")
        self.assertEqual(source["name"], self.connection.name)
        self.assertFalse(source["last_sync"])
        self.pages(1)
        self.connection._dda_pull(full=True)
        source = self.sources()[key]
        self.assertEqual(source["state"], "ok")
        self.assertEqual(
            source["last_sync"], self.connection.dda_sync_status_ids.last_date
        )
        self.assertEqual(source["action"]["res_id"], self.connection.id)
        dashboard = self.Debit.dda_dashboard()
        self.assertIn(key, [item["key"] for item in dashboard["sources"]])

    def test_a_connection_turned_off_by_the_bank_stays_as_an_error_source(self):
        self.enable()
        self.connection._dda_bank_disabled()
        self.assertFalse(self.connection.dda_enabled)
        source = self.sources()[source_key(self.connection)]
        self.assertEqual(source["state"], "error")
        self.assertIn("disabled", source["message"])
        # Once DDA is back, the status is ok and the source is a normal one.
        self.connection._dda_bank_enabled()
        self.assertEqual(self.sources()[source_key(self.connection)]["state"], "ok")

    def test_the_sources_of_other_companies_are_hidden(self):
        self.enable()
        debit_model = self.Debit.with_context(allowed_company_ids=[self.company_2.id])
        keys = [source["key"] for source in debit_model._dda_source_status()]
        self.assertNotIn(source_key(self.connection), keys)
