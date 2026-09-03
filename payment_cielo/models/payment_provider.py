# Copyright 2020 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
import pprint

import requests

from odoo import _, fields, models
from odoo.exceptions import ValidationError

from ..const import API_URLS, SUPPORTED_CURRENCIES
from ..utils import redact_card_data

_logger = logging.getLogger(__name__)


class PaymentProvider(models.Model):
    _inherit = "payment.provider"

    code = fields.Selection(
        selection_add=[("cielo", "Cielo")], ondelete={"cielo": "set default"}
    )
    cielo_merchant_id = fields.Char(
        string="Merchant Id",
        help="The store identifier provided by Cielo, in the GUID format.",
        required_if_provider="cielo",
        groups="base.group_system",
    )
    cielo_merchant_key = fields.Char(
        string="Merchant Key",
        help="The authentication key provided by Cielo, 40 characters long.",
        required_if_provider="cielo",
        groups="base.group_system",
    )
    cielo_soft_descriptor = fields.Char(
        string="Soft Descriptor",
        help="The name that appears on the credit card statement of the customer. "
        "Cielo limits it to 13 characters.",
    )

    # === COMPUTE METHODS === #

    def _compute_feature_support_fields(self):
        """Override of `payment` to enable additional features."""
        res = super()._compute_feature_support_fields()
        self.filtered(lambda p: p.code == "cielo").update(
            {
                "support_manual_capture": True,
                "support_refund": "full_only",
                "support_tokenization": True,
            }
        )
        return res

    # === BUSINESS METHODS === #

    def _get_compatible_providers(self, *args, currency_id=None, **kwargs):
        """Override of `payment` to filter out Cielo for unsupported currencies."""
        providers = super()._get_compatible_providers(
            *args, currency_id=currency_id, **kwargs
        )

        currency = self.env["res.currency"].browse(currency_id).exists()
        if currency and currency.name not in SUPPORTED_CURRENCIES:
            providers = providers.filtered(lambda p: p.code != "cielo")

        return providers

    def _get_validation_amount(self):
        """Override of `payment` to return the amount for Cielo validations.

        Cielo denies authorizations with a zero amount, so tokens are validated
        with the smallest amount that the acquirer accepts. The authorization is
        voided right away by the payment framework.
        """
        res = super()._get_validation_amount()
        if self.code != "cielo":
            return res
        return 1.0

    def _cielo_get_api_url(self, query=False):
        """Return the base URL of the Cielo API for the state of the provider.

        :param bool query: Whether the query API must be returned instead of the
                           transaction API.
        :return: The base URL of the API.
        :rtype: str
        """
        self.ensure_one()
        environment = "prod" if self.state == "enabled" else "test"
        return API_URLS[environment]["query" if query else "transaction"]

    def _cielo_get_api_headers(self):
        """Return the headers required by every call to the Cielo API.

        :return: The headers of the request.
        :rtype: dict
        :raise ValidationError: If the credentials of the provider are missing.
        """
        self.ensure_one()
        provider_sudo = self.sudo()
        if not provider_sudo.cielo_merchant_id or not provider_sudo.cielo_merchant_key:
            raise ValidationError(
                _("Cielo: The merchant credentials are not configured.")
            )
        return {
            "MerchantId": provider_sudo.cielo_merchant_id,
            "MerchantKey": provider_sudo.cielo_merchant_key,
            "Content-Type": "application/json",
        }

    def _cielo_make_request(self, endpoint, payload=None, method="POST", query=False):
        """Make a request to the Cielo API at the specified endpoint.

        :param str endpoint: The endpoint to be reached by the request.
        :param dict payload: The payload of the request.
        :param str method: The HTTP method of the request.
        :param bool query: Whether the request targets the query API.
        :return: The JSON-formatted content of the response.
        :rtype: dict
        :raise ValidationError: If an HTTP error occurs.
        """
        self.ensure_one()

        url = f"{self._cielo_get_api_url(query=query)}/{endpoint.strip('/')}"
        try:
            response = requests.request(
                method,
                url,
                json=payload,
                headers=self._cielo_get_api_headers(),
                timeout=60,
            )
            try:
                response.raise_for_status()
            except requests.exceptions.HTTPError:
                # The payload carries the card details: never log it as is.
                _logger.exception(
                    "invalid API request at %s with data:\n%s\nresponse status: %s",
                    url,
                    pprint.pformat(redact_card_data(payload)),
                    response.status_code,
                )
                raise ValidationError(
                    _(
                        "Cielo: The communication with the API failed. Cielo gave "
                        "us the following information: %s",
                        self._cielo_get_error_message(response),
                    )
                ) from None
        except requests.exceptions.RequestException:
            _logger.exception("unable to reach endpoint at %s", url)
            raise ValidationError(
                _("Cielo: Could not establish the connection to the API.")
            ) from None

        if not response.content:  # Cielo answers with an empty body on some calls.
            return {}
        try:
            return response.json()
        except ValueError:
            _logger.exception(
                "the API answered with a non-JSON body of %s bytes and status %s",
                len(response.content),
                response.status_code,
            )
            raise ValidationError(
                _("Cielo: The API answered with an unexpected response.")
            ) from None

    @staticmethod
    def _cielo_get_error_message(response):
        """Return a human readable message out of an error response of Cielo.

        Errors are returned as a list of ``{"Code": ..., "Message": ...}``, but
        the API also answers with plain text on some infrastructure errors.

        :param response: The response of the failed request.
        :return: The error message.
        :rtype: str
        """
        try:
            content = response.json()
        except ValueError:
            # A body that is not JSON may be echoing back the request, card
            # details included, so only its beginning is reported.
            return response.text[:200]
        if isinstance(content, list):
            return " ".join(
                f"{error.get('Code')}: {error.get('Message')}"
                for error in content
                if isinstance(error, dict)
            )
        return str(content)
