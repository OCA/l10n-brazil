# Copyright 2020 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from unittest.mock import patch

from odoo.exceptions import ValidationError
from odoo.tests import tagged
from odoo.tools import mute_logger

from odoo.addons.payment import utils as payment_utils
from odoo.addons.payment_cielo.const import (
    API_URLS,
    PAYMENT_STATUS_MAPPING,
    get_card_brand,
)

from .common import CieloCommon


@tagged("post_install", "-at_install")
class TestCieloProvider(CieloCommon):
    def test_feature_support(self):
        """The features supported by the Cielo API are enabled on the provider."""
        self.assertTrue(self.cielo.support_manual_capture)
        self.assertTrue(self.cielo.support_tokenization)
        self.assertEqual(self.cielo.support_refund, "full_only")
        self.assertFalse(self.cielo.support_express_checkout)

    def test_provider_is_compatible_with_brl_only(self):
        """Cielo settles in BRL only and must be filtered out for other currencies."""
        self.cielo.is_published = True
        compatible_providers = self.env["payment.provider"]._get_compatible_providers(
            self.company.id,
            self.partner.id,
            self.amount,
            currency_id=self.currency_brl.id,
        )
        self.assertIn(self.cielo, compatible_providers)

        compatible_providers = self.env["payment.provider"]._get_compatible_providers(
            self.company.id,
            self.partner.id,
            self.amount,
            currency_id=self.currency_usd.id,
        )
        self.assertNotIn(self.cielo, compatible_providers)

    def test_validation_amount_is_not_zero(self):
        """Cielo denies authorizations of zero, so validations use a real amount."""
        self.assertEqual(self.cielo._get_validation_amount(), 1.0)

    def test_api_url_depends_on_the_state(self):
        """The sandbox is used unless the provider is enabled."""
        self.cielo.state = "test"
        self.assertEqual(
            self.cielo._cielo_get_api_url(), API_URLS["test"]["transaction"]
        )
        self.assertEqual(
            self.cielo._cielo_get_api_url(query=True), API_URLS["test"]["query"]
        )

        self.cielo.state = "enabled"
        self.assertEqual(
            self.cielo._cielo_get_api_url(), API_URLS["prod"]["transaction"]
        )
        self.assertEqual(
            self.cielo._cielo_get_api_url(query=True), API_URLS["prod"]["query"]
        )

    def test_api_headers_carry_the_credentials(self):
        """The credentials of the provider authenticate every request."""
        headers = self.cielo._cielo_get_api_headers()
        self.assertEqual(headers["MerchantId"], self.cielo.cielo_merchant_id)
        self.assertEqual(headers["MerchantKey"], self.cielo.cielo_merchant_key)
        self.assertEqual(headers["Content-Type"], "application/json")

    def test_api_headers_require_the_credentials(self):
        """No request is made when the credentials are not configured."""
        self.cielo.write({"state": "disabled", "cielo_merchant_key": False})
        with self.assertRaises(ValidationError):
            self.cielo._cielo_get_api_headers()

    def test_error_message_of_a_failed_request(self):
        """The error codes returned by Cielo are reported to the user."""

        class ResponseStub:
            @staticmethod
            def json():
                return [
                    {"Code": 126, "Message": "Credit Card Expiration Date is invalid"}
                ]

        message = self.env["payment.provider"]._cielo_get_error_message(ResponseStub())
        self.assertEqual(message, "126: Credit Card Expiration Date is invalid")

    def test_error_message_of_a_non_json_response(self):
        """Infrastructure errors are reported as-is."""

        class ResponseStub:
            text = "Bad Gateway"

            @staticmethod
            def json():
                raise ValueError()

        message = self.env["payment.provider"]._cielo_get_error_message(ResponseStub())
        self.assertEqual(message, "Bad Gateway")

    def test_processing_values_include_an_access_token(self):
        """The inline form receives an access token to secure the payment route."""
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


@tagged("post_install", "-at_install")
class TestCieloConstants(CieloCommon):
    def test_every_documented_status_is_mapped(self):
        """Every status documented by Cielo is mapped to a transaction state."""
        mapped_statuses = [
            status
            for statuses in PAYMENT_STATUS_MAPPING.values()
            for status in statuses
        ]
        for status in (0, 1, 2, 3, 10, 11, 12, 13, 20):
            self.assertIn(status, mapped_statuses)
        self.assertEqual(
            len(mapped_statuses), len(set(mapped_statuses)), "a status is mapped twice"
        )

    def test_card_brand_detection(self):
        """The brand sent to Cielo is detected from the card number."""
        self.assertEqual(get_card_brand("4024 0071 9769 2931"), "Visa")
        self.assertEqual(get_card_brand("5457631234567890"), "Master")
        self.assertEqual(get_card_brand("340000000000009"), "Amex")
        self.assertEqual(get_card_brand("3841001234567890"), "Hipercard")
        self.assertEqual(get_card_brand("6062821234567890"), "Hipercard")
        self.assertEqual(get_card_brand("6362971234567890"), "Elo")
        self.assertEqual(get_card_brand("3566001234567890"), "JCB")

    def test_card_brand_of_elo_prevails_over_the_generic_prefixes(self):
        """Elo BINs must not be detected as Visa or Master."""
        self.assertEqual(get_card_brand("4011781234567890"), "Elo")
        self.assertEqual(get_card_brand("5041751234567890"), "Elo")

    def test_card_brand_of_an_unsupported_card(self):
        """An unknown card number has no brand."""
        self.assertIsNone(get_card_brand("9999999999999999"))
        self.assertIsNone(get_card_brand(""))
        self.assertIsNone(get_card_brand(None))

    def test_expiration_date_formatting(self):
        """Cielo expects the expiration date in the MM/YYYY format."""
        transaction = self.env["payment.transaction"]
        self.assertEqual(transaction._cielo_format_expiration_date("02/30"), "02/2030")
        self.assertEqual(
            transaction._cielo_format_expiration_date("02 / 30"), "02/2030"
        )
        self.assertEqual(transaction._cielo_format_expiration_date("0230"), "02/2030")
        self.assertEqual(
            transaction._cielo_format_expiration_date("12/2030"), "12/2030"
        )

    def test_invalid_expiration_date(self):
        """An expiration date that cannot be parsed is rejected before the request."""
        transaction = self.env["payment.transaction"]
        for expiry in ("", "2", "13/30", "00/30", "02/2/30"):
            with self.assertRaises(ValidationError):
                transaction._cielo_format_expiration_date(expiry)
