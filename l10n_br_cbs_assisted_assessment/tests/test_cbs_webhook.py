# Copyright 2026 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import json

from odoo.tests import tagged
from odoo.tests.common import HttpCase
from odoo.tools import mute_logger

from ..constants import WEBHOOK_ROUTE

WEBHOOK_LOG = "odoo.addons.l10n_br_cbs_assisted_assessment.controllers.webhook"


@tagged("post_install", "-at_install")
class TestCbsWebhook(HttpCase):
    def setUp(self):
        super().setUp()
        # Binds the session to the test database: the callback is anonymous, so
        # without it the instance cannot tell which database to dispatch to.
        self.authenticate(None, None)
        self.company = self.env.company
        self.company.action_cbs_assessment_rotate_webhook_token()
        self.token = self.company.cbs_assessment_webhook_token
        self.request_record = self.env["l10n_br_assessment.request"].create(
            {
                "company_id": self.company.id,
                "tribute": "cbs",
                "service": "debits",
                "state": "requested",
                "ticket": "692b7b25-44cb-4415-8625-2b9522dd7933.B5E08D55",
            }
        )
        self.env.flush_all()

    def _url(self, token=None):
        return f"{WEBHOOK_ROUTE}/{token or self.token}"

    def _post(self, payload, token=None):
        return self.url_open(
            self._url(token),
            data=json.dumps(payload),
            headers={"Content-Type": "application/json"},
        )

    def test_get_answers_the_url_validation(self):
        """The gateway validates the callback with HEAD before accepting."""
        response = self.url_open(self._url())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ready")

    @mute_logger(WEBHOOK_LOG)
    def test_unknown_token_is_rejected(self):
        response = self.url_open(self._url("not-a-token"))
        self.assertEqual(response.status_code, 404)

    def test_callback_registers_the_signed_url(self):
        response = self._post(
            {
                "tiqueteSolicitacao": self.request_record.ticket,
                "urlAssinada": "https://storage.example.com/f.json?X-Amz-Signature=x",
                "urlAssinadaExpiraEm": "2099-01-01T00:00:00Z",
            }
        )
        self.assertEqual(response.status_code, 200)
        self.request_record.invalidate_recordset()
        self.assertEqual(self.request_record.state, "notified")
        self.assertTrue(self.request_record.signed_url)

    def test_callback_registers_the_error(self):
        response = self._post(
            {
                "tiqueteSolicitacao": self.request_record.ticket,
                "codigoErro": "APURACAO-408",
                "mensagemErro": "Timeout",
            }
        )
        self.assertEqual(response.status_code, 200)
        self.request_record.invalidate_recordset()
        self.assertEqual(self.request_record.state, "error")

    @mute_logger(WEBHOOK_LOG)
    def test_unknown_ticket_is_rejected(self):
        response = self._post({"tiqueteSolicitacao": "other"})
        self.assertEqual(response.status_code, 404)

    def test_invalid_payload_is_rejected(self):
        response = self.url_open(
            self._url(),
            data="{not json",
            headers={"Content-Type": "application/json"},
        )
        self.assertEqual(response.status_code, 400)
