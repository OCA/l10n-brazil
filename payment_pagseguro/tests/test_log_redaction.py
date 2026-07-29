# Copyright 2020 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from contextlib import contextmanager
from unittest.mock import patch

import requests

from odoo.exceptions import ValidationError
from odoo.tests import tagged

from odoo.addons.payment_pagseguro.utils import mask_card_number, redact_card_data

from .common import PagseguroCommon

_MODULE_LOGGER = "odoo.addons.payment_pagseguro"
_WATCHED_LOGGERS = (
    "odoo.addons.payment_pagseguro.models.payment_provider",
    "odoo.addons.payment_pagseguro.models.payment_transaction",
)
ENCRYPTED_CARD = "encrypted-card-credential"
HOLDER = "CARDHOLDER TEST"
TAX_ID = "23130935000198"


class _ResponseStub:
    def __init__(self, status_code=200, body=b"", json_data=None):
        self.status_code = status_code
        self.content = body
        self.text = body.decode(errors="replace")
        self._json = json_data

    def json(self):
        if self._json is None:
            raise ValueError("no json")
        return self._json

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.exceptions.HTTPError(f"HTTP {self.status_code}")


@tagged("post_install", "-at_install")
class TestPagseguroLogRedaction(PagseguroCommon):
    """The payment credentials of the customer must never reach a log."""

    @contextmanager
    def _capture_logs(self):
        """Collect everything the module logs, whatever the log level is."""
        records = []

        class _Collector(logging.Handler):
            def emit(self, record):
                records.append(f"{record.name} {record.getMessage()}")

        handler = _Collector()
        module_logger = logging.getLogger(_MODULE_LOGGER)
        watched = [logging.getLogger(name) for name in _WATCHED_LOGGERS]
        previous_levels = [logger.level for logger in watched]
        module_logger.addHandler(handler)
        for logger in watched:
            logger.setLevel(logging.INFO)
        try:
            yield records
        finally:
            module_logger.removeHandler(handler)
            for logger, level in zip(watched, previous_levels, strict=True):
                logger.setLevel(level)

    def test_redact_drops_the_encrypted_card(self):
        """The encrypted card is a credential: it may be replayed."""
        redacted = redact_card_data({"card": {"encrypted": ENCRYPTED_CARD}})
        self.assertNotIn(ENCRYPTED_CARD, str(redacted))

    def test_redact_drops_the_holder_and_the_personal_data(self):
        redacted = redact_card_data(
            {
                "customer": {"tax_id": TAX_ID, "email": "buyer@example.com"},
                "card": {"holder": {"name": HOLDER}},
            }
        )
        self.assertNotIn(TAX_ID, str(redacted))
        self.assertNotIn("buyer@example.com", str(redacted))
        self.assertNotIn(HOLDER, str(redacted))

    def test_redact_masks_a_card_number(self):
        redacted = redact_card_data({"card": {"number": "4024007197692931"}})
        self.assertNotIn("4024007197692931", str(redacted))

    def test_redact_keeps_the_rest_of_the_payload(self):
        payload = {"reference_id": "S00001", "charges": [{"amount": {"value": 1000}}]}
        self.assertEqual(redact_card_data(payload), payload)

    def test_mask_of_a_short_value(self):
        self.assertEqual(mask_card_number("12"), "***")

    def test_failed_request_does_not_log_the_credentials(self):
        """A 4xx from PagBank must not turn the payload into a log entry."""
        self.partner.vat = TAX_ID
        tx = self._create_transaction(flow="direct")
        response = _ResponseStub(status_code=400, body=b'{"error_messages":[]}')
        with patch(
            "odoo.addons.payment_pagseguro.models.payment_provider.requests.request",
            return_value=response,
        ):
            with self._capture_logs() as records:
                with self.assertRaises(ValidationError):
                    tx._pagseguro_create_order(
                        encrypted_card=ENCRYPTED_CARD, card_holder=HOLDER
                    )

        logged = "\n".join(records)
        self.assertIn("invalid API request", logged, "the failure was not logged")
        self.assertNotIn(ENCRYPTED_CARD, logged, "the encrypted card reached the log")
        self.assertNotIn(HOLDER, logged, "the holder reached the log")
        self.assertNotIn(TAX_ID, logged, "the tax id reached the log")

    def test_successful_request_does_not_log_the_credentials(self):
        tx = self._create_transaction(flow="direct")
        response_content = self._order_response(store=True)
        response_content["charges"][0]["payment_method"]["card"]["holder"] = {
            "name": HOLDER
        }
        with self._patch_request(response_content):
            with self._capture_logs() as records:
                tx._pagseguro_create_order(encrypted_card=ENCRYPTED_CARD)

        logged = "\n".join(records)
        self.assertTrue(records, "nothing was logged")
        self.assertNotIn(HOLDER, logged, "the holder reached the log")
