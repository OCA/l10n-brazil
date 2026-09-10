# Copyright 2023 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64
import contextlib
import logging
import os
import pprint
import tempfile
from datetime import timedelta

import requests

from odoo import _, fields, models
from odoo.exceptions import ValidationError

from ..const import (
    DEFAULT_EXPIRATION,
    OAUTH_SCOPE,
    PSP_CONFIG,
    SUPPORTED_CURRENCIES,
)
from ..utils import redact_personal_data

_logger = logging.getLogger(__name__)

# The token is renewed slightly before it expires, to absorb the round trip.
TOKEN_EXPIRATION_MARGIN = 60


class PaymentProvider(models.Model):
    _inherit = "payment.provider"

    code = fields.Selection(
        selection_add=[("bacenpix", "Pix")],
        ondelete={"bacenpix": "set default"},
    )
    bacenpix_psp = fields.Selection(
        selection=[(psp, config["name"]) for psp, config in PSP_CONFIG.items()],
        string="Pix Provider",
        help="The bank that holds the Pix account. The Pix API itself is "
        "standardized by the Central Bank: only the base URL, the way the "
        "token is obtained and the need for a certificate change.",
        default="bb",
        required_if_provider="bacenpix",
    )
    bacenpix_key = fields.Char(
        string="Pix Key",
        help="The Pix key that receives the payments, as registered with the "
        "PSP: a CPF/CNPJ, a phone number, an email or a random key.",
        required_if_provider="bacenpix",
        groups="base.group_system",
    )
    bacenpix_client_id = fields.Char(
        string="Client ID",
        required_if_provider="bacenpix",
        groups="base.group_system",
    )
    bacenpix_client_secret = fields.Char(
        string="Client Secret",
        required_if_provider="bacenpix",
        groups="base.group_system",
    )
    bacenpix_app_key = fields.Char(
        string="Application Key",
        help="The developer application key, required by the gateway of the "
        "Banco do Brasil (gw-dev-app-key).",
        groups="base.group_system",
    )
    bacenpix_certificate = fields.Binary(
        string="Certificate",
        help="The client certificate in the PEM format, required by the PSPs "
        "that demand mutual TLS.",
        groups="base.group_system",
    )
    bacenpix_private_key = fields.Binary(
        string="Private Key",
        help="The private key of the client certificate, in the PEM format.",
        groups="base.group_system",
    )
    bacenpix_expiration = fields.Integer(
        string="Expiration (s)",
        help="The number of seconds a charge stays payable.",
        default=DEFAULT_EXPIRATION,
    )
    bacenpix_token = fields.Char(groups="base.group_system", readonly=True)
    bacenpix_token_expiry = fields.Datetime(groups="base.group_system", readonly=True)

    # === BUSINESS METHODS === #

    def _get_compatible_providers(self, *args, currency_id=None, **kwargs):
        """Override of `payment` to filter out Pix for unsupported currencies."""
        providers = super()._get_compatible_providers(
            *args, currency_id=currency_id, **kwargs
        )

        currency = self.env["res.currency"].browse(currency_id).exists()
        if currency and currency.name not in SUPPORTED_CURRENCIES:
            providers = providers.filtered(lambda p: p.code != "bacenpix")

        return providers

    def _bacenpix_get_psp_config(self):
        """Return the configuration of the PSP of the provider.

        :return: The configuration of the PSP.
        :rtype: dict
        :raise ValidationError: If no PSP is selected.
        """
        self.ensure_one()
        config = PSP_CONFIG.get(self.bacenpix_psp)
        if not config:
            raise ValidationError(_("Pix: No Pix provider is selected."))
        return config

    def _bacenpix_get_environment(self):
        """Return the environment matching the state of the provider."""
        self.ensure_one()
        return "prod" if self.state == "enabled" else "test"

    def _bacenpix_get_api_url(self):
        """Return the base URL of the Pix API of the PSP.

        :return: The base URL of the API.
        :rtype: str
        """
        self.ensure_one()
        config = self._bacenpix_get_psp_config()
        return config["api_url"][self._bacenpix_get_environment()]

    @contextlib.contextmanager
    def _bacenpix_certificate_files(self):
        """Yield the paths of the client certificate and of its private key.

        The files are written with restricted permissions and removed as soon as
        the request is over. `None` is yielded when the PSP does not require
        mutual TLS and no certificate is configured.

        :return: The tuple expected by the `cert` argument of `requests`.
        :rtype: tuple|None
        :raise ValidationError: If the PSP requires a certificate that is missing.
        """
        self.ensure_one()
        provider_sudo = self.sudo()
        config = self._bacenpix_get_psp_config()

        if (
            not provider_sudo.bacenpix_certificate
            or not provider_sudo.bacenpix_private_key
        ):
            if config["mutual_tls"]:
                raise ValidationError(
                    _(
                        "Pix: %s requires a client certificate and its private "
                        "key to be configured.",
                        config["name"],
                    )
                )
            yield None
            return

        paths = []
        try:
            for content in (
                provider_sudo.bacenpix_certificate,
                provider_sudo.bacenpix_private_key,
            ):
                file_descriptor, path = tempfile.mkstemp(suffix=".pem")
                with os.fdopen(file_descriptor, "wb") as pem_file:
                    pem_file.write(base64.b64decode(content))
                os.chmod(path, 0o600)
                paths.append(path)
            yield tuple(paths)
        finally:
            for path in paths:
                with contextlib.suppress(OSError):
                    os.remove(path)

    def _bacenpix_get_token(self):
        """Return a valid OAuth token, requesting a new one when needed.

        The token is cached on the provider until shortly before it expires, as
        the PSPs rate limit the token endpoint.

        :return: The access token.
        :rtype: str
        """
        self.ensure_one()
        provider_sudo = self.sudo()

        now = fields.Datetime.now()
        if (
            provider_sudo.bacenpix_token
            and provider_sudo.bacenpix_token_expiry
            and provider_sudo.bacenpix_token_expiry > now
        ):
            return provider_sudo.bacenpix_token

        config = self._bacenpix_get_psp_config()
        url = config["token_url"][self._bacenpix_get_environment()]
        data = {"grant_type": "client_credentials", "scope": OAUTH_SCOPE}
        auth = None
        if config["token_auth"] == "basic":
            auth = (
                provider_sudo.bacenpix_client_id,
                provider_sudo.bacenpix_client_secret,
            )
        else:
            data["client_id"] = provider_sudo.bacenpix_client_id
            data["client_secret"] = provider_sudo.bacenpix_client_secret

        try:
            with self._bacenpix_certificate_files() as cert:
                response = requests.post(
                    url,
                    data=data,
                    auth=auth,
                    cert=cert,
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                    timeout=60,
                )
            response.raise_for_status()
            content = response.json()
        except requests.exceptions.RequestException:
            _logger.exception("unable to get a token at %s", url)
            raise ValidationError(
                _("Pix: Could not authenticate with %s.", config["name"])
            ) from None
        except ValueError:
            _logger.exception("the token endpoint answered with a non-JSON body")
            raise ValidationError(
                _(
                    "Pix: %s answered the token request with an unexpected response.",
                    config["name"],
                )
            ) from None

        token = content.get("access_token")
        if not token:
            raise ValidationError(
                _("Pix: %s did not return an access token.", config["name"])
            )
        provider_sudo.write(
            {
                "bacenpix_token": token,
                "bacenpix_token_expiry": now
                + timedelta(
                    seconds=max(
                        int(content.get("expires_in", 600)) - TOKEN_EXPIRATION_MARGIN,
                        TOKEN_EXPIRATION_MARGIN,
                    )
                ),
            }
        )
        return token

    def _bacenpix_make_request(self, endpoint, payload=None, method="POST"):
        """Make a request to the Pix API of the PSP at the specified endpoint.

        :param str endpoint: The endpoint to be reached by the request.
        :param dict payload: The payload of the request.
        :param str method: The HTTP method of the request.
        :return: The JSON-formatted content of the response.
        :rtype: dict
        :raise ValidationError: If an HTTP error occurs.
        """
        self.ensure_one()

        config = self._bacenpix_get_psp_config()
        url = f"{self._bacenpix_get_api_url()}/{endpoint.strip('/')}"
        params = {}
        if config["app_key_param"] and self.sudo().bacenpix_app_key:
            params[config["app_key_param"]] = self.sudo().bacenpix_app_key

        headers = {
            "Authorization": f"Bearer {self._bacenpix_get_token()}",
            "Content-Type": "application/json",
        }
        try:
            with self._bacenpix_certificate_files() as cert:
                response = requests.request(
                    method,
                    url,
                    json=payload,
                    params=params,
                    headers=headers,
                    cert=cert,
                    timeout=60,
                )
            try:
                response.raise_for_status()
            except requests.exceptions.HTTPError:
                _logger.exception(
                    "invalid API request at %s with data:\n%s\nHTTP status: %s",
                    url,
                    pprint.pformat(redact_personal_data(payload)),
                    response.status_code,
                )
                raise ValidationError(
                    _(
                        "Pix: The communication with the API failed. %(psp)s gave "
                        "us the following information: %(error)s",
                        psp=config["name"],
                        error=self._bacenpix_get_error_message(response),
                    )
                ) from None
        except requests.exceptions.RequestException:
            _logger.exception("unable to reach endpoint at %s", url)
            raise ValidationError(
                _("Pix: Could not establish the connection to %s.", config["name"])
            ) from None

        if not response.content:
            return {}
        try:
            return response.json()
        except ValueError:
            _logger.exception(
                "the API answered with a non-JSON body, HTTP status: %s",
                response.status_code,
            )
            raise ValidationError(
                _("Pix: The API answered with an unexpected response.")
            ) from None

    @staticmethod
    def _bacenpix_get_error_message(response):
        """Return a human readable message out of an error response.

        The Pix API answers errors with an RFC 7807 problem detail, holding a
        `title`, a `detail` and, for the invalid fields, a `violacoes` list.

        :param response: The response of the failed request.
        :return: The error message.
        :rtype: str
        """
        try:
            content = response.json()
        except ValueError:
            return response.text
        if not isinstance(content, dict):
            return str(content)
        message = " ".join(
            part for part in (content.get("title"), content.get("detail")) if part
        )
        violations = content.get("violacoes") or []
        for violation in violations:
            if isinstance(violation, dict):
                message += (
                    f" [{violation.get('propriedade')}: {violation.get('razao')}]"
                )
        return message or str(content)
