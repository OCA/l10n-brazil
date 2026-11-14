# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""The refresh token renewed by the bank (BTG) is persisted at once."""

import json
from unittest.mock import patch
from urllib.parse import parse_qs

import httpx
from brbank.erros import ErroBrbank

from odoo.tests import HttpCase, tagged
from odoo.tools import mute_logger

from odoo.addons.l10n_br_bank_connection.models.connection import RENEWED_TOKENS

from .common import BrbankCommon, BrbankTransactionCase

LOGGER = "odoo.addons.l10n_br_bank_connection.models.connection"
STORE_LOGGER = "odoo.addons.l10n_br_bank_connection.utils.token_store"
LOCK_TIMEOUT = (
    "odoo.addons.l10n_br_bank_connection.models.connection.APART_LOCK_TIMEOUT_MS"
)
BTG_SETTINGS = {
    "cnpj_empresa": "91300766000147",
    "agencia": "1234",
    "conta_corrente": "1234567",
}


class BtgBankMixin:
    """A BTG provider and a fake BTG that rotates the refresh token."""

    def _setup_btg(self):
        self.sent_tokens = []
        self.next_tokens = ["rt-new", "rt-newer"]
        self.collection_status = 200

        def handler(request):
            if request.url.path.endswith("/oauth2/token"):
                form = parse_qs(request.content.decode())
                self.assertEqual(form["grant_type"], ["refresh_token"])
                self.sent_tokens.append(form["refresh_token"][0])
                return httpx.Response(
                    200,
                    json={
                        "access_token": "access-token",
                        "expires_in": 3600,
                        "refresh_token": self.next_tokens.pop(0),
                    },
                )
            if self.collection_status != 200:
                return httpx.Response(
                    self.collection_status, json={"Message": "refused"}
                )
            return httpx.Response(
                200,
                content=b"%PDF-1.4 btg",
                headers={"Content-Type": "application/pdf"},
            )

        self.transport = httpx.MockTransport(handler)

    def _btg_provider(self, connection=None):
        values = {
            "refresh_token": "rt-old",
            "extra_config": json.dumps(BTG_SETTINGS),
        }
        if connection:
            # A connection committed by the demo data, to lock its row.
            connection.write(
                dict(
                    values,
                    client_id="client-id",
                    client_secret="client-secret",
                    api_base_url_override=False,
                    token_url_override=False,
                    environment="test",
                )
            )
            provider = self.env.ref(
                "l10n_br_payment_brbank.payment_provider_brbank_btg"
            )
            provider.write({"brbank_connection_id": connection.id, "state": "test"})
            return provider
        return self._create_provider("btg", connection_values=values)

    def _btg_pdf(self, provider):
        return provider.with_context(brbank_http_transport=self.transport)._brbank_run(
            lambda adapter: adapter.obter_pdf("collection-1")
        )


@tagged("post_install", "-at_install")
class TestRefreshTokenCommitted(BtgBankMixin, BrbankCommon, HttpCase):
    """Own cursor path: `HttpCase` runs in test mode, so the cursor opened by
    the callback is a test cursor on the same connection and the commit
    lands where the test can read it."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._setup_brbank()

    def setUp(self):
        super().setUp()
        self._setup_btg()

    def _stored_token(self, connection):
        with self.registry.cursor() as cr:
            cr.execute(
                "SELECT refresh_token FROM l10n_br_bank_connection_connection "
                "WHERE id = %s",
                (connection.id,),
            )
            return cr.fetchone()[0]

    def _expire_access_token(self, connection):
        with self.registry.cursor() as cr:
            cr.execute(
                "UPDATE l10n_br_bank_connection_token SET expires_at = 0 "
                "WHERE connection_id = %s",
                (connection.id,),
            )

    def test_renewed_token_committed_and_reused(self):
        provider = self._btg_provider()
        connection = provider.brbank_connection_id
        self.assertEqual(self._btg_pdf(provider), b"%PDF-1.4 btg")
        self.assertEqual(self.sent_tokens, ["rt-old"])
        self.assertEqual(self._stored_token(connection), "rt-new")
        # The next call renews with the new token, not the snapshot one.
        self.assertEqual(self.env.cr.cache[RENEWED_TOKENS][connection.id], "rt-new")
        # The access token is stored: no new renewal while it is valid.
        self._btg_pdf(provider)
        self.assertEqual(self.sent_tokens, ["rt-old"])
        self._expire_access_token(connection)
        self._btg_pdf(provider)
        self.assertEqual(self.sent_tokens, ["rt-old", "rt-new"])
        self.assertEqual(self._stored_token(connection), "rt-newer")
        _adapter_class, config = provider._brbank_prepare_adapter()
        self.assertEqual(config.refresh_token, "rt-newer")
        self.assertNotIn("rt-newer", repr(config))

    def test_renewed_token_survives_a_failed_call(self):
        provider = self._btg_provider()
        connection = provider.brbank_connection_id
        self.collection_status = 400
        # Not `assertRaises`: it rolls back a savepoint the callback cursor shares.
        try:
            self._btg_pdf(provider)
        except ErroBrbank:
            refused = True
        else:
            refused = False
        self.assertTrue(refused)
        self.assertEqual(self.sent_tokens, ["rt-old"])
        self.assertEqual(self._stored_token(connection), "rt-new")
        # The failure is remembered, but a refused title is not a broken connection.
        self.assertTrue(connection.last_error)
        self.assertEqual(connection.state, "connected")


@tagged("post_install", "-at_install")
class TestRefreshTokenFallback(BtgBankMixin, BrbankTransactionCase):
    """Without test mode the callback opens a real cursor: it cannot see a
    connection of the test transaction, nor lock a row this transaction wrote,
    so the token goes to the current transaction (with a warning)."""

    def setUp(self):
        super().setUp()
        self._setup_btg()

    def _assert_fallback(self, provider, reason, sent="rt-old"):
        connection = provider.brbank_connection_id
        with (
            mute_logger(STORE_LOGGER),
            self.assertLogs(LOGGER, level="WARNING") as logs,
        ):
            self._btg_pdf(provider)
        output = "\n".join(logs.output)
        self.assertIn("current transaction only", output)
        self.assertIn(reason, output)
        self.assertNotIn("rt-new", output)
        self.assertEqual(self.sent_tokens, [sent])
        self.assertEqual(connection.refresh_token, "rt-new")
        self.assertNotIn(connection.id, self.env.cr.cache.get(RENEWED_TOKENS, {}))

    def test_connection_not_committed(self):
        self._assert_fallback(self._btg_provider(), "not committed yet")

    def test_row_locked_by_the_caller(self):
        connection = self.env.ref(
            "l10n_br_bank_connection.connection_demo_btg_simulator"
        )
        # The library reads the committed refresh token: a demo one would win.
        with self.env.registry.cursor() as cr:
            cr.execute(
                "SELECT refresh_token FROM l10n_br_bank_connection_connection"
                " WHERE id = %s",
                (connection.id,),
            )
            committed = cr.fetchone()[0]
        provider = self._btg_provider(connection)
        with patch(LOCK_TIMEOUT, 300):
            self._assert_fallback(
                provider, "LockNotAvailable", sent=committed or "rt-old"
            )
