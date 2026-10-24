# Copyright 2020 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from contextlib import contextmanager
from unittest.mock import patch

import requests

from odoo.exceptions import ValidationError
from odoo.tests import tagged

from odoo.addons.payment_cielo.utils import mask_card_number, redact_card_data

from .common import CieloCommon

_MODULE_LOGGER = "odoo.addons.payment_cielo"
_WATCHED_LOGGERS = (
    "odoo.addons.payment_cielo.models.payment_provider",
    "odoo.addons.payment_cielo.models.payment_transaction",
)
CARD_NUMBER = "4024007197692931"
SECURITY_CODE = "123"
HOLDER = "CARDHOLDER TEST"


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
class TestCieloLogRedaction(CieloCommon):
    """The card details are sent to Cielo, so they must never reach a log.

    A log file is not a place where a card number may be stored, and a security
    code may not be stored anywhere at all.
    """

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

    def test_redact_drops_the_security_code(self):
        payload = {"Payment": {"CreditCard": {"SecurityCode": SECURITY_CODE}}}
        redacted = redact_card_data(payload)
        self.assertNotIn(
            SECURITY_CODE, str(redacted), "the security code survived the redaction"
        )

    def test_redact_masks_the_card_number(self):
        redacted = redact_card_data({"CardNumber": CARD_NUMBER})
        self.assertNotIn(CARD_NUMBER, str(redacted))
        self.assertEqual(redacted["CardNumber"], "***2931")

    def test_redact_drops_the_holder_and_the_expiration(self):
        redacted = redact_card_data({"Holder": HOLDER, "ExpirationDate": "02/2030"})
        self.assertNotIn(HOLDER, str(redacted))
        self.assertNotIn("02/2030", str(redacted))

    def test_redact_drops_the_personal_data_of_the_payer(self):
        """The log of a gateway does not need the email nor the document."""
        redacted = redact_card_data(
            {"Customer": {"Email": "buyer@example.com", "Identity": "19186747058"}}
        )
        self.assertNotIn("buyer@example.com", str(redacted))
        self.assertNotIn("19186747058", str(redacted))

    def test_redact_walks_lists_and_nested_payloads(self):
        redacted = redact_card_data(
            {"items": [{"card": {"cardNumber": CARD_NUMBER, "cvv": SECURITY_CODE}}]}
        )
        self.assertNotIn(CARD_NUMBER, str(redacted))
        self.assertNotIn(SECURITY_CODE, str(redacted))

    def test_redact_keeps_the_rest_of_the_payload(self):
        payload = {"MerchantOrderId": "S00001", "Payment": {"Amount": 111111}}
        self.assertEqual(redact_card_data(payload), payload)

    def test_mask_of_a_short_value(self):
        self.assertEqual(mask_card_number("12"), "***")
        self.assertEqual(mask_card_number(None), "***")

    def test_failed_request_does_not_log_the_card(self):
        """A 4xx from Cielo must not turn the payload into a log entry."""
        tx = self._create_transaction(flow="direct")
        card_data = dict(self.card_data, card_holder=HOLDER)
        response = _ResponseStub(status_code=400, body=b'[{"Code":126}]')
        with patch(
            "odoo.addons.payment_cielo.models.payment_provider.requests.request",
            return_value=response,
        ):
            with self._capture_logs() as records:
                with self.assertRaises(ValidationError):
                    tx._cielo_create_sale(card_data=card_data)

        logged = "\n".join(records)
        self.assertIn("invalid API request", logged, "the failure was not logged")
        self.assertNotIn(CARD_NUMBER, logged, "the card number reached the log")
        self.assertNotIn(
            f"'{SECURITY_CODE}'", logged, "the security code reached the log"
        )
        self.assertNotIn(HOLDER, logged, "the holder reached the log")
        self.assertNotIn(
            "norbert.buyer@example.com", logged, "the email reached the log"
        )

    def test_successful_request_does_not_log_the_card(self):
        """The response of Cielo carries card details back: redact it too."""
        tx = self._create_transaction(flow="direct")
        response_content = self._sale_response(save_card=True)
        response_content["Payment"]["CreditCard"]["Holder"] = HOLDER
        with self._patch_request(response_content):
            with self._capture_logs() as records:
                tx._cielo_create_sale(card_data=self.card_data)

        logged = "\n".join(records)
        self.assertTrue(records, "nothing was logged")
        self.assertNotIn(HOLDER, logged, "the holder reached the log")
        self.assertNotIn(self.card_token, logged, "the card token reached the log")

    def test_capture_and_void_do_not_log_the_card(self):
        self.cielo.capture_manually = True
        tx = self._create_transaction(
            flow="direct", state="authorized", provider_reference=self.payment_id
        )
        response = self._operation_response(status=2)
        response["CreditCard"] = {"CardNumber": CARD_NUMBER, "Holder": HOLDER}
        with self._patch_request(response):
            with self._capture_logs() as records:
                tx._send_capture_request()

        logged = "\n".join(records)
        self.assertTrue(records, "nothing was logged")
        self.assertNotIn(CARD_NUMBER, logged)
        self.assertNotIn(HOLDER, logged)
