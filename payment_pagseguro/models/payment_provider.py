# Copyright 2020 KMEE
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
        selection_add=[("pagseguro", "PagSeguro")],
        ondelete={"pagseguro": "set default"},
    )
    pagseguro_token = fields.Char(
        string="API Token",
        help="The token generated in the PagBank account, under "
        "Vendas Online > Integrações > Token.",
        required_if_provider="pagseguro",
        groups="base.group_system",
    )
    pagseguro_soft_descriptor = fields.Char(
        string="Soft Descriptor",
        help="The name that appears on the credit card statement of the "
        "customer. PagBank limits it to 17 characters.",
    )

    # === COMPUTE METHODS === #

    def _compute_feature_support_fields(self):
        """Override of `payment` to enable additional features."""
        res = super()._compute_feature_support_fields()
        self.filtered(lambda p: p.code == "pagseguro").update(
            {
                "support_manual_capture": True,
                "support_refund": "full_only",
                "support_tokenization": True,
            }
        )
        return res

    # === BUSINESS METHODS === #

    def _get_compatible_providers(self, *args, currency_id=None, **kwargs):
        """Override of `payment` to filter out PagSeguro for other currencies."""
        providers = super()._get_compatible_providers(
            *args, currency_id=currency_id, **kwargs
        )

        currency = self.env["res.currency"].browse(currency_id).exists()
        if currency and currency.name not in SUPPORTED_CURRENCIES:
            providers = providers.filtered(lambda p: p.code != "pagseguro")

        return providers

    def _pagseguro_get_api_url(self):
        """Return the base URL of the API for the state of the provider.

        :return: The base URL of the API.
        :rtype: str
        """
        self.ensure_one()
        return API_URLS["prod" if self.state == "enabled" else "test"]

    def _pagseguro_get_api_headers(self):
        """Return the headers required by every call to the API.

        :return: The headers of the request.
        :rtype: dict
        :raise ValidationError: If the token of the provider is missing.
        """
        self.ensure_one()
        token = self.sudo().pagseguro_token
        if not token:
            raise ValidationError(_("PagSeguro: The API token is not configured."))
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "x-api-version": "4.0",
        }

    def _pagseguro_make_request(self, endpoint, payload=None, method="POST"):
        """Make a request to the PagBank API at the specified endpoint.

        :param str endpoint: The endpoint to be reached by the request.
        :param dict payload: The payload of the request.
        :param str method: The HTTP method of the request.
        :return: The JSON-formatted content of the response.
        :rtype: dict
        :raise ValidationError: If an HTTP error occurs.
        """
        self.ensure_one()

        url = f"{self._pagseguro_get_api_url()}/{endpoint.strip('/')}"
        try:
            response = requests.request(
                method,
                url,
                json=payload,
                headers=self._pagseguro_get_api_headers(),
                timeout=60,
            )
            try:
                response.raise_for_status()
            except requests.exceptions.HTTPError:
                # The payload carries the payment credentials of the customer.
                _logger.exception(
                    "invalid API request at %s with data:\n%s\nresponse status: %s",
                    url,
                    pprint.pformat(redact_card_data(payload)),
                    response.status_code,
                )
                raise ValidationError(
                    _(
                        "PagSeguro: The communication with the API failed. "
                        "PagBank gave us the following information: %s",
                        self._pagseguro_get_error_message(response),
                    )
                ) from None
        except requests.exceptions.RequestException:
            _logger.exception("unable to reach endpoint at %s", url)
            raise ValidationError(
                _("PagSeguro: Could not establish the connection to the API.")
            ) from None

        if not response.content:
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
                _("PagSeguro: The API answered with an unexpected response.")
            ) from None

    @staticmethod
    def _pagseguro_get_error_message(response):
        """Return a human readable message out of an error response.

        Errors are returned in an `error_messages` list holding a `code`, a
        `description` and the `parameter_name` at fault.

        :param response: The response of the failed request.
        :return: The error message.
        :rtype: str
        """
        try:
            content = response.json()
        except ValueError:
            # A body that is not JSON may be echoing back the request.
            return response.text[:200]
        errors = content.get("error_messages") or []
        if not errors:
            return str(content)
        return " ".join(
            f"{error.get('code')}: {error.get('description')} "
            f"({error.get('parameter_name')})"
            for error in errors
            if isinstance(error, dict)
        )
