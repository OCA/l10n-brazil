# Copyright 2023 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from unittest.mock import patch

import requests

from odoo.exceptions import ValidationError
from odoo.tests import tagged

from odoo.addons.payment_bacen_pix.const import PSP_CONFIG

from .common import PROVIDER_PATH, ApiResponse, BacenPixCommon, collect_logs


@tagged("post_install", "-at_install")
class TestBacenPixApiLayer(BacenPixCommon):
    """The requests to the Pix API, which the other tests mock away."""

    def setUp(self):
        super().setUp()
        token_patcher = patch(
            f"{PROVIDER_PATH}.PaymentProvider._bacenpix_get_token",
            return_value="token",
        )
        token_patcher.start()
        self.addCleanup(token_patcher.stop)

    def test_request_carries_the_token_and_the_application_key(self):
        """The BB gateway expects the developer key as a query parameter."""
        with patch(
            f"{PROVIDER_PATH}.requests.request",
            return_value=ApiResponse({"txid": self.txid}),
        ) as request_mock:
            content = self.bacenpix._bacenpix_make_request(
                "/cob/1234", {"valor": {"original": "10.00"}}, method="PUT"
            )

        self.assertEqual(content, {"txid": self.txid})
        self.assertEqual(request_mock.call_args.args[0], "PUT")
        self.assertEqual(
            request_mock.call_args.args[1],
            f"{PSP_CONFIG['bb']['api_url']['test']}/cob/1234",
        )
        self.assertEqual(
            request_mock.call_args.kwargs["headers"]["Authorization"], "Bearer token"
        )
        self.assertEqual(
            request_mock.call_args.kwargs["params"],
            {PSP_CONFIG["bb"]["app_key_param"]: "dummy-app-key"},
        )

    def test_request_without_an_application_key_sends_no_parameter(self):
        """The key is only sent when it is configured."""
        self.bacenpix.bacenpix_app_key = False
        with patch(
            f"{PROVIDER_PATH}.requests.request",
            return_value=ApiResponse({"txid": self.txid}),
        ) as request_mock:
            self.bacenpix._bacenpix_make_request("/cob/1234", method="GET")

        self.assertEqual(request_mock.call_args.kwargs["params"], {})

    def test_empty_response_is_read_as_an_empty_content(self):
        """A 204, as answered by a refund, has no body to parse."""
        with patch(
            f"{PROVIDER_PATH}.requests.request",
            return_value=ApiResponse(status_code=204, body=""),
        ):
            self.assertEqual(
                self.bacenpix._bacenpix_make_request("/cob/1234", method="GET"), {}
            )

    def test_http_error_is_reported_with_the_problem_details(self):
        """The user gets the reason the PSP refused the charge."""
        response = ApiResponse(
            {
                "title": "Cobrança inválida",
                "detail": "A requisição está fora do padrão.",
            },
            status_code=400,
            raises=requests.exceptions.HTTPError("HTTP 400"),
        )
        with patch(f"{PROVIDER_PATH}.requests.request", return_value=response):
            with self.assertRaises(ValidationError) as error:
                self.bacenpix._bacenpix_make_request("/cob/1234", {})

        self.assertIn("Cobrança inválida", error.exception.args[0])

    def test_connection_error_is_reported_as_such(self):
        """A PSP that cannot be reached is not a charge that was refused."""
        with patch(
            f"{PROVIDER_PATH}.requests.request",
            side_effect=requests.exceptions.ConnectionError("no route to host"),
        ):
            with self.assertRaises(ValidationError) as error:
                self.bacenpix._bacenpix_make_request("/cob/1234", {})

        self.assertIn("connection", error.exception.args[0].lower())

    def test_non_json_response_is_rejected(self):
        """An HTML error page from a proxy is not a charge."""
        with patch(
            f"{PROVIDER_PATH}.requests.request",
            return_value=ApiResponse(body="<html>gateway timeout</html>"),
        ):
            with self.assertRaises(ValidationError):
                self.bacenpix._bacenpix_make_request("/cob/1234", method="GET")

    def test_non_json_response_does_not_reach_the_log(self):
        """The body of an unexpected response can hold anything: keep it out."""
        with collect_logs(f"{PROVIDER_PATH}") as records:
            with patch(
                f"{PROVIDER_PATH}.requests.request",
                return_value=ApiResponse(body="<html>gateway timeout</html>"),
            ):
                with self.assertRaises(ValidationError):
                    self.bacenpix._bacenpix_make_request("/cob/1234", method="GET")

        logged = "\n".join(records)
        self.assertIn("non-JSON body", logged)
        self.assertNotIn("gateway timeout", logged)


@tagged("post_install", "-at_install")
class TestBacenPixToken(BacenPixCommon):
    """The failures of the OAuth token endpoint."""

    def test_authentication_failure_is_reported(self):
        with patch(
            f"{PROVIDER_PATH}.requests.post",
            side_effect=requests.exceptions.ConnectionError("no route to host"),
        ):
            with self.assertRaises(ValidationError) as error:
                self.bacenpix._bacenpix_get_token()

        self.assertIn("authenticate", error.exception.args[0].lower())

    def test_non_json_token_response_is_rejected(self):
        with patch(
            f"{PROVIDER_PATH}.requests.post",
            return_value=ApiResponse(body="<html>forbidden</html>"),
        ):
            with self.assertRaises(ValidationError):
                self.bacenpix._bacenpix_get_token()

    def test_response_without_a_token_is_rejected(self):
        """A 200 that carries no token is still a failed authentication."""
        with patch(
            f"{PROVIDER_PATH}.requests.post",
            return_value=ApiResponse({"expires_in": 600}),
        ):
            with self.assertRaises(ValidationError) as error:
                self.bacenpix._bacenpix_get_token()

        self.assertIn("access token", error.exception.args[0].lower())
