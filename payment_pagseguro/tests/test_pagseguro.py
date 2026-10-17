# Copyright 2020 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from unittest.mock import patch

from odoo.exceptions import ValidationError
from odoo.tests import tagged
from odoo.tools import mute_logger

from odoo.addons.payment import utils as payment_utils
from odoo.addons.payment_pagseguro.const import API_URLS, PAYMENT_STATUS_MAPPING

from .common import PagseguroCommon


@tagged("post_install", "-at_install")
class TestPagseguroProvider(PagseguroCommon):
    def test_feature_support(self):
        """The features supported by the PagBank API are enabled."""
        self.assertTrue(self.pagseguro.support_manual_capture)
        self.assertTrue(self.pagseguro.support_tokenization)
        self.assertEqual(self.pagseguro.support_refund, "full_only")

    def test_provider_is_compatible_with_brl_only(self):
        """PagBank settles in BRL only."""
        self.pagseguro.is_published = True
        providers = self.env["payment.provider"]._get_compatible_providers(
            self.company.id,
            self.partner.id,
            self.amount,
            currency_id=self.currency_brl.id,
        )
        self.assertIn(self.pagseguro, providers)

        providers = self.env["payment.provider"]._get_compatible_providers(
            self.company.id,
            self.partner.id,
            self.amount,
            currency_id=self.currency_usd.id,
        )
        self.assertNotIn(self.pagseguro, providers)

    def test_api_url_depends_on_the_state(self):
        """The sandbox is used unless the provider is enabled."""
        self.pagseguro.state = "test"
        self.assertEqual(self.pagseguro._pagseguro_get_api_url(), API_URLS["test"])

        self.pagseguro.state = "enabled"
        self.assertEqual(self.pagseguro._pagseguro_get_api_url(), API_URLS["prod"])

    def test_api_headers_carry_the_token(self):
        """The token of the provider authenticates every request."""
        headers = self.pagseguro._pagseguro_get_api_headers()
        self.assertEqual(headers["Authorization"], "Bearer dummy-token")
        self.assertEqual(headers["x-api-version"], "4.0")

    def test_api_headers_require_the_token(self):
        """No request is made when the token is not configured."""
        self.pagseguro.write({"state": "disabled", "pagseguro_token": False})
        with self.assertRaises(ValidationError):
            self.pagseguro._pagseguro_get_api_headers()

    def test_error_message_of_a_failed_request(self):
        """The error messages returned by PagBank are reported to the user."""

        class ResponseStub:
            @staticmethod
            def json():
                return {
                    "error_messages": [
                        {
                            "code": "40002",
                            "description": "must be numeric",
                            "parameter_name": "charges[0].amount.value",
                        }
                    ]
                }

        message = self.env["payment.provider"]._pagseguro_get_error_message(
            ResponseStub()
        )
        self.assertEqual(message, "40002: must be numeric (charges[0].amount.value)")

    def test_every_documented_status_is_mapped(self):
        """Every charge status documented by PagBank is mapped."""
        mapped = [s for statuses in PAYMENT_STATUS_MAPPING.values() for s in statuses]
        for status in (
            "AUTHORIZED",
            "PAID",
            "DECLINED",
            "CANCELED",
            "IN_ANALYSIS",
            "WAITING",
        ):
            self.assertIn(status, mapped)
        self.assertEqual(len(mapped), len(set(mapped)), "a status is mapped twice")

    def test_processing_values_include_an_access_token(self):
        """The inline form receives an access token to secure the route."""
        tx = self._create_transaction(flow="direct")
        with mute_logger("odoo.addons.payment.models.payment_transaction"), patch(
            "odoo.addons.payment.utils.generate_access_token",
            new=self._generate_test_access_token,
        ):
            processing_values = tx._get_processing_values()

        with patch(
            "odoo.addons.payment.utils.generate_access_token",
            new=self._generate_test_access_token,
        ):
            self.assertTrue(
                payment_utils.check_access_token(
                    processing_values["access_token"], self.reference, self.partner.id
                )
            )
