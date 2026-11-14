# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import json
from unittest.mock import patch

from brbank.erros import Validacao

from odoo.exceptions import UserError
from odoo.tests import HttpCase, tagged

from .common import ConnectionCommon

CONTROLLER_LOGGER = "odoo.addons.l10n_br_bank_connection.controllers.main"


@tagged("post_install", "-at_install")
class TestWebhook(ConnectionCommon, HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._setup_connection()

    def setUp(self):
        super().setUp()
        self.connection = self._create_connection()

    def _post(self, body="[]", connection=None, token=None, connection_id=None):
        connection = connection or self.connection
        return self.url_open(
            "/l10n_br_bank_connection/webhook/{}/{}".format(
                connection_id or connection.id,
                connection.webhook_token if token is None else token,
            ),
            data=body,
            headers={"Content-Type": "application/json"},
        )

    def _hook(self, **kwargs):
        return patch.object(
            type(self.connection), "_l10n_br_bank_handle_webhook", **kwargs
        )

    def test_wrong_token_unknown_and_archived_look_the_same(self):
        wrong = self._post(token="wrong-token")
        unknown = self._post(connection_id=999999)
        self.connection.active = False
        archived = self._post()
        for response in (wrong, unknown, archived):
            self.assertEqual(response.status_code, 404)
            self.assertEqual(response.text, "")

    def test_only_post_is_accepted(self):
        response = self.url_open(
            f"/l10n_br_bank_connection/webhook/{self.connection.id}/"
            f"{self.connection.webhook_token}"
        )
        self.assertEqual(response.status_code, 405)

    def test_unknown_event_is_not_an_error(self):
        response = self._post(json.dumps([{"evento": "something.new"}]))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(any(response.json().values()))

    def test_the_domains_answer_with_their_counts(self):
        with self._hook(return_value={"collection": 2, "dda": 1}) as hook:
            response = self._post('{"a": 1}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"collection": 2, "dda": 1})
        args = hook.call_args.args
        self.assertEqual(args[0], b'{"a": 1}')
        self.assertIn("Content-Type", args[1])

    def test_a_refused_payload_is_400_and_the_body_is_not_logged(self):
        secret_body = '{"cpf": "291.250.832-01"}'
        for error in (Validacao("bad"), UserError("bad"), ValueError("bad")):
            with self._hook(side_effect=error):
                with self.assertLogs(CONTROLLER_LOGGER, "INFO") as logs:
                    response = self._post(secret_body)
            self.assertEqual(response.status_code, 400)
            self.assertNotIn("291.250", "\n".join(logs.output))

    def test_token_rotation_stops_the_old_url(self):
        old_token = self.connection.webhook_token
        self.connection.action_rotate_webhook_token()
        self.assertEqual(self._post(token=old_token).status_code, 404)
        self.assertEqual(self._post().status_code, 200)
