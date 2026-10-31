# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64
import hashlib
from datetime import timedelta
from unittest.mock import patch
from urllib.parse import parse_qs, urlparse

from brbank.erros import Validacao

from odoo import fields
from odoo.tests import HttpCase, new_test_user, tagged

from ..models.connection import PENDING_REFRESH_TOKEN
from .common import ConnectionCommon

START = "/l10n_br_bank_connection/oauth/start/{}"
CALLBACK = "/l10n_br_bank_connection/oauth/callback"


def _challenge(verifier):
    digest = hashlib.sha256(verifier.encode()).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode()


@tagged("post_install", "-at_install")
class TestOAuth(ConnectionCommon, HttpCase):
    """Authorization code with PKCE, with the OAuth functions of the adapter
    replaced by fakes (no bank, no network)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._setup_connection()

    def setUp(self):
        super().setUp()
        self.connection = self._create_connection(
            scopes="openid direct-debit", refresh_token=False
        )
        self.calls = {"authorize": [], "exchange": []}
        self.exchange_result = {
            "refresh_token": "rt-from-bank",
            "access_token": "at",
            "expires_in": 3600,
        }

        def authorize(config, redirect_uri, state, code_challenge, escopos):
            self.calls["authorize"].append(
                {
                    "config": config,
                    "redirect_uri": redirect_uri,
                    "state": state,
                    "challenge": code_challenge,
                    "scopes": escopos,
                }
            )
            return (
                "https://bank.example/authorize?"
                f"state={state}&code_challenge={code_challenge}"
            )

        async def exchange(config, code, redirect_uri, code_verifier):
            self.calls["exchange"].append(
                {
                    "config": config,
                    "code": code,
                    "redirect_uri": redirect_uri,
                    "verifier": code_verifier,
                }
            )
            if isinstance(self.exchange_result, Exception):
                raise self.exchange_result
            return self.exchange_result

        patcher = patch.object(
            type(self.connection),
            "_l10n_br_bank_oauth_functions",
            lambda connection: (authorize, exchange),
        )
        patcher.start()
        self.addCleanup(patcher.stop)

    def _start(self):
        self.authenticate("admin", "admin")
        return self.url_open(START.format(self.connection.id), allow_redirects=False)

    def _callback(self, **params):
        return self.url_open(
            CALLBACK + "?" + "&".join(f"{k}={v}" for k, v in params.items()),
            allow_redirects=False,
        )

    def test_start_redirects_to_the_bank_with_state_and_pkce(self):
        response = self._start()
        self.assertEqual(response.status_code, 303)
        query = parse_qs(urlparse(response.headers["Location"]).query)
        call = self.calls["authorize"][0]
        self.connection.invalidate_recordset()
        connection = self.connection
        self.assertEqual(query["state"], [connection.oauth_state])
        self.assertGreaterEqual(len(connection.oauth_state), 32)
        self.assertGreaterEqual(len(connection.oauth_verifier), 43)
        self.assertEqual(call["challenge"], _challenge(connection.oauth_verifier))
        self.assertEqual(query["code_challenge"], [call["challenge"]])
        self.assertTrue(call["redirect_uri"].endswith(CALLBACK))
        self.assertEqual(call["scopes"], "openid direct-debit")
        # No refresh token yet: the configuration still builds.
        self.assertEqual(call["config"].refresh_token, PENDING_REFRESH_TOKEN)
        self.assertGreater(
            connection.oauth_expires, fields.Datetime.now() + timedelta(minutes=9)
        )

    def test_start_is_for_connection_administrators_only(self):
        new_test_user(self.env, login="plain-user", groups="base.group_user")
        self.authenticate("plain-user", "plain-user")
        response = self.url_open(
            START.format(self.connection.id), allow_redirects=False
        )
        self.assertEqual(response.status_code, 403)
        self.assertFalse(self.calls["authorize"])

    def test_start_requires_a_login(self):
        self.authenticate(None, None)
        response = self.url_open(
            START.format(self.connection.id), allow_redirects=False
        )
        self.assertIn(response.status_code, (303, 401, 403))
        self.assertFalse(self.calls["authorize"])

    def _started(self):
        self._start()
        self.connection.invalidate_recordset()
        return self.connection.oauth_state, self.connection.oauth_verifier

    def test_callback_saves_the_refresh_token(self):
        state, verifier = self._started()
        response = self._callback(code="the-code", state=state)
        self.assertEqual(response.status_code, 303)
        self.assertIn(
            f"id={self.connection.id}&model=l10n_br_bank_connection.connection",
            response.headers["Location"],
        )
        call = self.calls["exchange"][0]
        self.assertEqual(call["code"], "the-code")
        self.assertEqual(call["verifier"], verifier)
        self.assertTrue(call["redirect_uri"].endswith(CALLBACK))
        self.connection.invalidate_recordset()
        connection = self.connection
        self.assertEqual(connection.refresh_token, "rt-from-bank")
        self.assertEqual(connection.state, "connected")
        self.assertFalse(connection.last_error)
        # Single use.
        self.assertFalse(connection.oauth_state or connection.oauth_verifier)
        replay = self._callback(code="the-code", state=state)
        self.assertEqual(replay.status_code, 400)
        self.assertEqual(len(self.calls["exchange"]), 1)

    def test_callback_with_the_wrong_state_is_refused(self):
        self._started()
        for state in ("not-the-state", ""):
            response = self._callback(code="c", state=state)
            self.assertEqual(response.status_code, 400)
        self.assertFalse(self.calls["exchange"])

    def test_callback_after_the_validity_is_refused(self):
        state, _verifier = self._started()
        self.connection.oauth_expires = fields.Datetime.now() - timedelta(minutes=1)
        response = self._callback(code="c", state=state)
        self.assertEqual(response.status_code, 400)
        self.assertFalse(self.calls["exchange"])

    def test_callback_is_for_connection_administrators_only(self):
        state, _verifier = self._started()
        new_test_user(self.env, login="plain-user", groups="base.group_user")
        self.authenticate("plain-user", "plain-user")
        response = self._callback(code="c", state=state)
        self.assertEqual(response.status_code, 403)
        self.assertFalse(self.calls["exchange"])

    def test_the_bank_refusing_the_code_keeps_the_connection_as_it_was(self):
        state, _verifier = self._started()
        self.exchange_result = Validacao("code refused")
        response = self._callback(code="bad", state=state)
        self.assertEqual(response.status_code, 303)
        self.connection.invalidate_recordset()
        self.assertFalse(self.connection.refresh_token)
        self.assertEqual(self.connection.state, "draft")
        self.assertIn("refused", self.connection.last_error)

    def test_a_consent_denied_at_the_bank_is_remembered(self):
        state, _verifier = self._started()
        response = self._callback(error="access_denied", state=state)
        self.assertEqual(response.status_code, 303)
        self.assertFalse(self.calls["exchange"])
        self.connection.invalidate_recordset()
        self.assertFalse(self.connection.oauth_state)
        self.assertTrue(self.connection.last_error)
