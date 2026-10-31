# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import json
from decimal import Decimal

from brbank import StatusCanonico

from odoo.tests import HttpCase, tagged

from .common import BrbankCommon
from .fake_bank import reset_bank


@tagged("post_install", "-at_install")
class TestBrbankWebhook(BrbankCommon, HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._setup_brbank()

    def setUp(self):
        super().setUp()
        reset_bank()
        self.invoice = self._create_invoice()
        self.tx = self._brbank_txs(self.invoice)[0]
        self.Event = self.env["l10n_br.brbank.event"]

    def _webhook_token(self, provider):
        return provider.brbank_connection_id.webhook_token

    def _post(self, payload, provider=None, token=None):
        provider = provider or self.provider
        token = token if token is not None else self._webhook_token(provider)
        return self.url_open(
            f"/payment/brbank/webhook/{provider.id}/{token}",
            data=json.dumps(payload),
            headers={"Content-Type": "application/json"},
        )

    def _event_payload(self, status="LIQUIDADO", paid="300.00"):
        return [{"ref": self.tx.provider_reference, "status": status, "paid": paid}]

    def test_wrong_token_is_404_without_details(self):
        response = self._post(self._event_payload(), token="wrong-token")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.text, "")
        self.assertFalse(self.Event.search([]))

    def test_unknown_provider_looks_like_a_wrong_token(self):
        response = self.url_open(
            "/payment/brbank/webhook/999999/whatever",
            data="[]",
            headers={"Content-Type": "application/json"},
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.text, "")

    def test_disabled_provider_is_404(self):
        token = self._webhook_token(self.provider)
        self.provider.state = "disabled"
        response = self._post(self._event_payload(), token=token)
        self.assertEqual(response.status_code, 404)

    def test_connection_route_stores_the_same_events(self):
        connection = self.provider.brbank_connection_id
        response = self.url_open(
            f"/l10n_br_bank_connection/webhook/{connection.id}/"
            f"{connection.webhook_token}",
            data=json.dumps(self._event_payload()),
            headers={"Content-Type": "application/json"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"received": 1, "new": 1})
        event = self.Event.search([])
        self.assertEqual(event.connection_id, connection)
        # The alias answers the same notification as already received.
        self.assertEqual(
            self._post(self._event_payload()).json(), {"received": 1, "new": 0}
        )

    def test_unreadable_payload_is_400(self):
        response = self.url_open(
            f"/payment/brbank/webhook/{self.provider.id}/"
            f"{self._webhook_token(self.provider)}",
            data="not json",
            headers={"Content-Type": "application/json"},
        )
        self.assertEqual(response.status_code, 400)

    def test_event_stored_masked_and_deduplicated(self):
        response = self._post(self._event_payload())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"received": 1, "new": 1})
        event = self.Event.search([])
        self.assertEqual(len(event), 1)
        self.assertEqual(event.reference, self.tx.provider_reference)
        self.assertEqual(event.event_type, "LIQUIDADO")
        # Same notification again: received, not stored twice.
        response = self._post(self._event_payload())
        self.assertEqual(response.json(), {"received": 1, "new": 0})
        self.assertEqual(self.Event.search_count([]), 1)

    def test_event_settles_only_after_the_bank_query(self):
        self._post(self._event_payload())
        self.assertEqual(self.tx.state, "authorized")
        self.Event._cron_process_events()
        event = self.Event.search([])
        self.assertEqual(event.state, "done")
        self.assertEqual(event.transaction_id, self.tx)
        self.assertEqual(self.tx.state, "authorized")
        self.assertIn(("consultar", self.tx.provider_reference), self.bank["calls"])
        # The bank confirms: the safety net cron settles the title.
        self._set_bank_status(self.tx, StatusCanonico.LIQUIDADO, Decimal("300.00"))
        self.env["payment.transaction"]._cron_brbank_reconcile()
        self.assertEqual(self.tx.state, "done")
        self.assertTrue(self.tx.move_line_id.reconciled)

    def test_event_processed_with_the_bank_confirmation(self):
        self._set_bank_status(self.tx, StatusCanonico.LIQUIDADO, Decimal("300.00"))
        self._post(self._event_payload())
        self.Event._cron_process_events()
        self.assertEqual(self.tx.state, "done")

    def test_event_of_unknown_title_is_ignored(self):
        self._post([{"ref": "B-unknown", "status": "LIQUIDADO"}])
        self.Event._cron_process_events()
        self.assertEqual(self.Event.search([]).state, "ignored")

    def test_portal_invoice_page_lists_the_titles(self):
        token = self.invoice._portal_ensure_token()
        response = self.url_open(f"/my/invoices/{self.invoice.id}?access_token={token}")
        self.assertEqual(response.status_code, 200)
        for tx in self._brbank_txs(self.invoice):
            self.assertIn(tx.digitable_line, response.text)
            self.assertIn(f"/brbank/{tx.id}?access_token=", response.text)

    def test_portal_boleto_with_the_invoice_token(self):
        token = self.invoice._portal_ensure_token()
        url = f"/my/invoices/{self.invoice.id}/brbank/{self.tx.id}"
        response = self.url_open(f"{url}?access_token={token}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["Content-Type"], "application/pdf")
        self.assertTrue(response.content.startswith(b"%PDF"))
        response = self.url_open(f"{url}?access_token=wrong", allow_redirects=False)
        self.assertNotEqual(response.status_code, 200)
