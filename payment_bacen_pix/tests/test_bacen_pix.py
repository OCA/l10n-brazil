# Copyright 2023 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from unittest.mock import patch

from odoo import fields
from odoo.exceptions import ValidationError
from odoo.tests import tagged

from odoo.addons.payment_bacen_pix.const import PSP_CONFIG

from .common import ApiResponse, BacenPixCommon


@tagged("post_install", "-at_install")
class TestBacenPixProvider(BacenPixCommon):
    def test_provider_is_compatible_with_brl_only(self):
        """Pix settles in BRL only."""
        self.bacenpix.is_published = True
        providers = self.env["payment.provider"]._get_compatible_providers(
            self.company.id,
            self.partner.id,
            self.amount,
            currency_id=self.currency_brl.id,
        )
        self.assertIn(self.bacenpix, providers)

        providers = self.env["payment.provider"]._get_compatible_providers(
            self.company.id,
            self.partner.id,
            self.amount,
            currency_id=self.currency_usd.id,
        )
        self.assertNotIn(self.bacenpix, providers)

    def test_api_url_depends_on_the_psp_and_on_the_state(self):
        """Only the base URL changes from one PSP to another."""
        self.bacenpix.write({"bacenpix_psp": "bb", "state": "test"})
        self.assertEqual(
            self.bacenpix._bacenpix_get_api_url(), PSP_CONFIG["bb"]["api_url"]["test"]
        )

        self.bacenpix.state = "enabled"
        self.assertEqual(
            self.bacenpix._bacenpix_get_api_url(), PSP_CONFIG["bb"]["api_url"]["prod"]
        )

        self.bacenpix.write({"bacenpix_psp": "inter", "state": "test"})
        self.assertEqual(
            self.bacenpix._bacenpix_get_api_url(),
            PSP_CONFIG["inter"]["api_url"]["test"],
        )

    def test_token_is_requested_with_basic_auth_for_the_bb(self):
        """The BB expects the credentials in the authorization header."""
        self.bacenpix.bacenpix_psp = "bb"
        with patch(
            "odoo.addons.payment_bacen_pix.models.payment_provider.requests.post",
            return_value=ApiResponse({"access_token": "tok", "expires_in": 600}),
        ) as post_mock:
            token = self.bacenpix._bacenpix_get_token()

        self.assertEqual(token, "tok")
        self.assertEqual(
            post_mock.call_args.args[0], PSP_CONFIG["bb"]["token_url"]["test"]
        )
        self.assertEqual(
            post_mock.call_args.kwargs["auth"],
            ("dummy-client-id", "dummy-client-secret"),
        )
        self.assertNotIn("client_secret", post_mock.call_args.kwargs["data"])

    def test_token_is_requested_in_the_body_for_the_inter(self):
        """The Inter expects the credentials in the body of the request."""
        self.bacenpix.write(
            {
                "bacenpix_psp": "inter",
                "bacenpix_certificate": b"Y2VydA==",
                "bacenpix_private_key": b"a2V5",
            }
        )
        with patch(
            "odoo.addons.payment_bacen_pix.models.payment_provider.requests.post",
            return_value=ApiResponse({"access_token": "tok", "expires_in": 600}),
        ) as post_mock:
            self.bacenpix._bacenpix_get_token()

        self.assertIsNone(post_mock.call_args.kwargs["auth"])
        self.assertEqual(
            post_mock.call_args.kwargs["data"]["client_secret"], "dummy-client-secret"
        )
        self.assertEqual(len(post_mock.call_args.kwargs["cert"]), 2)

    def test_token_is_cached_until_it_expires(self):
        """The token endpoint is not called again while the token is valid."""
        with patch(
            "odoo.addons.payment_bacen_pix.models.payment_provider.requests.post",
            return_value=ApiResponse({"access_token": "tok", "expires_in": 600}),
        ) as post_mock:
            self.bacenpix._bacenpix_get_token()
            self.bacenpix._bacenpix_get_token()

        self.assertEqual(post_mock.call_count, 1)

    def test_expired_token_is_renewed(self):
        """A token that has expired is requested again."""
        self.bacenpix.write(
            {
                "bacenpix_token": "old-token",
                "bacenpix_token_expiry": fields.Datetime.subtract(
                    fields.Datetime.now(), minutes=5
                ),
            }
        )
        with patch(
            "odoo.addons.payment_bacen_pix.models.payment_provider.requests.post",
            return_value=ApiResponse({"access_token": "new-token", "expires_in": 600}),
        ):
            self.assertEqual(self.bacenpix._bacenpix_get_token(), "new-token")

    def test_mutual_tls_certificate_is_required_by_the_inter(self):
        """The PSPs that demand mutual TLS refuse to run without a certificate."""
        self.bacenpix.write(
            {
                "bacenpix_psp": "inter",
                "bacenpix_certificate": False,
                "bacenpix_private_key": False,
            }
        )
        with self.assertRaises(ValidationError):
            with self.bacenpix._bacenpix_certificate_files():
                pass

    def test_no_certificate_is_needed_by_the_bb(self):
        """The BB works without a client certificate."""
        self.bacenpix.bacenpix_psp = "bb"
        with self.bacenpix._bacenpix_certificate_files() as cert:
            self.assertIsNone(cert)

    def test_certificate_files_are_removed_after_use(self):
        """The private key does not stay on the disk."""
        self.bacenpix.write(
            {
                "bacenpix_psp": "inter",
                "bacenpix_certificate": b"Y2VydA==",
                "bacenpix_private_key": b"a2V5",
            }
        )
        import os

        with self.bacenpix._bacenpix_certificate_files() as cert:
            paths = list(cert)
            self.assertTrue(all(os.path.exists(path) for path in paths))
        self.assertFalse(any(os.path.exists(path) for path in paths))

    def test_error_message_of_a_failed_request(self):
        """The problem details returned by the API are reported to the user."""
        response = ApiResponse(
            {
                "title": "Cobrança inválida",
                "detail": "A requisição está fora do padrão.",
                "violacoes": [
                    {"razao": "chave não encontrada", "propriedade": "chave"}
                ],
            }
        )
        message = self.env["payment.provider"]._bacenpix_get_error_message(response)
        self.assertIn("Cobrança inválida", message)
        self.assertIn("[chave: chave não encontrada]", message)

    def test_error_message_of_a_non_json_response(self):
        """The body is the only information left when it is not a problem detail."""
        response = ApiResponse(body="502 Bad Gateway")
        self.assertEqual(
            self.env["payment.provider"]._bacenpix_get_error_message(response),
            "502 Bad Gateway",
        )

    def test_error_message_of_a_json_list(self):
        """The API of a PSP may answer a list instead of a problem detail."""
        response = ApiResponse(["erro"])
        self.assertEqual(
            self.env["payment.provider"]._bacenpix_get_error_message(response),
            "['erro']",
        )

    def test_unknown_psp_is_rejected(self):
        """A provider without a PSP cannot reach any API."""
        # The field is required by the framework, so it is emptied in the
        # database to reproduce a provider that was configured by a module.
        self.env.cr.execute(
            "UPDATE payment_provider SET bacenpix_psp = NULL WHERE id = %s",
            (self.bacenpix.id,),
        )
        self.bacenpix.invalidate_recordset(["bacenpix_psp"])
        with self.assertRaises(ValidationError):
            self.bacenpix._bacenpix_get_api_url()
