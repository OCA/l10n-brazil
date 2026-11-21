# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
import secrets
from datetime import timedelta
from urllib.parse import urlencode

import requests

from odoo import fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

MELHORENVIO_URLS = {
    "sandbox": "https://sandbox.melhorenvio.com.br",
    "production": "https://melhorenvio.com.br",
}
MELHORENVIO_TIMEOUT = 30
MELHORENVIO_CALLBACK = "/melhorenvio/oauth/callback"
MELHORENVIO_SCOPES = (
    "shipping-calculate shipping-cancel shipping-checkout shipping-companies "
    "shipping-generate shipping-preview shipping-print shipping-share "
    "shipping-tracking cart-read cart-write orders-read users-read"
)
# The access token lasts 30 days; renew it when it has less than this left.
MELHORENVIO_REFRESH_MARGIN = timedelta(days=2)


class MelhorEnvioAccount(models.Model):
    _name = "melhorenvio.account"
    _description = "Melhor Envio Account"
    _check_company_auto = True

    name = fields.Char(required=True)

    active = fields.Boolean(default=True)

    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company
    )

    environment = fields.Selection(
        [("sandbox", "Sandbox"), ("production", "Production")],
        required=True,
        default="sandbox",
    )

    contact_email = fields.Char(
        string="Technical Contact E-mail",
        required=True,
        help="Melhor Envio requires the application name and a contact "
        "e-mail in the User-Agent header of every request.",
    )

    client_id = fields.Char(
        string="Client ID",
        help="Client ID of the application registered at the Melhor Envio "
        "panel (Integrações > Área Dev.).",
    )

    client_secret = fields.Char(groups="base.group_system")

    redirect_uri = fields.Char(
        string="Redirect URL",
        help="Exactly the redirect URL registered in the Melhor Envio "
        "application. Leave empty to use the address of this Odoo.",
    )

    token = fields.Char(
        string="Access Token",
        groups="base.group_system",
        copy=False,
        help="Filled by the authorization. A token generated at the Melhor "
        "Envio panel can be pasted here instead.",
    )

    refresh_token = fields.Char(groups="base.group_system", copy=False)

    token_expiry = fields.Datetime(
        string="Token Valid Until", readonly=True, copy=False
    )

    oauth_state = fields.Char(groups="base.group_system", copy=False)

    carrier_ids = fields.One2many(
        "delivery.carrier", "melhorenvio_account_id", string="Services"
    )

    def _base_url(self):
        self.ensure_one()
        return MELHORENVIO_URLS[self.environment]

    def _get_redirect_uri(self):
        self.ensure_one()
        return self.redirect_uri or (
            self.get_base_url().rstrip("/") + MELHORENVIO_CALLBACK
        )

    def action_authorize(self):
        """Send the user to Melhor Envio to authorize the application."""
        self.ensure_one()
        account = self.sudo()
        if not (account.client_id and account.client_secret):
            raise UserError(
                self.env._(
                    "Set the Client ID and the Secret of the Melhor Envio "
                    "application."
                )
            )
        account.oauth_state = secrets.token_urlsafe(24)
        query = urlencode(
            {
                "client_id": account.client_id,
                "redirect_uri": account._get_redirect_uri(),
                "response_type": "code",
                "state": account.oauth_state,
                "scope": MELHORENVIO_SCOPES,
            }
        )
        return {
            "type": "ir.actions.act_url",
            "url": f"{account._base_url()}/oauth/authorize?{query}",
            "target": "self",
        }

    def _exchange_token(self, grant):
        """Trade an authorization code or a refresh token for an access
        token."""
        self.ensure_one()
        account = self.sudo()
        payload = {
            **grant,
            "client_id": account.client_id,
            "client_secret": account.client_secret,
            "redirect_uri": account._get_redirect_uri(),
        }
        try:
            response = requests.post(
                account._base_url() + "/oauth/token",
                json=payload,
                headers={
                    "Accept": "application/json",
                    "User-Agent": f"Odoo ({account.contact_email})",
                },
                timeout=MELHORENVIO_TIMEOUT,
            )
            data = response.json()
        except (requests.RequestException, ValueError) as error:
            _logger.warning("Melhor Envio: token request failed: %s", error)
            raise UserError(
                self.env._("Melhor Envio could not be reached, try again later.")
            ) from error
        if response.status_code != 200 or not data.get("access_token"):
            raise UserError(
                self.env._(
                    "Melhor Envio refused the authorization: %(message)s",
                    message=data.get("message")
                    or data.get("error_description")
                    or data,
                )
            )
        account.write(
            {
                "token": data["access_token"],
                "refresh_token": data.get("refresh_token"),
                "token_expiry": fields.Datetime.now()
                + timedelta(seconds=int(data.get("expires_in") or 0)),
                "oauth_state": False,
            }
        )

    def _refresh_token_if_needed(self):
        self.ensure_one()
        account = self.sudo()
        if (
            account.refresh_token
            and account.token_expiry
            and account.token_expiry - MELHORENVIO_REFRESH_MARGIN
            < fields.Datetime.now()
        ):
            account._exchange_token(
                {"grant_type": "refresh_token", "refresh_token": account.refresh_token}
            )

    def _headers(self, authenticated=True):
        self.ensure_one()
        account = self.sudo()
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": f"Odoo ({account.contact_email})",
        }
        if authenticated:
            account._refresh_token_if_needed()
            if not account.token:
                raise UserError(
                    self.env._(
                        "Authorize the Melhor Envio account %(account)s first.",
                        account=account.name,
                    )
                )
            headers["Authorization"] = f"Bearer {account.token}"
        return headers

    def _request(self, method, endpoint, payload=None, authenticated=True):
        self.ensure_one()
        headers = self._headers(authenticated=authenticated)
        try:
            response = requests.request(
                method,
                self._base_url() + endpoint,
                json=payload,
                headers=headers,
                timeout=MELHORENVIO_TIMEOUT,
            )
        except requests.RequestException as error:
            _logger.warning("Melhor Envio: %s %s failed: %s", method, endpoint, error)
            raise UserError(
                self.env._("Melhor Envio could not be reached, try again later.")
            ) from error
        if response.status_code == 401:
            raise UserError(self.env._("Melhor Envio refused the token (HTTP 401)."))
        try:
            data = response.json()
        except ValueError as error:
            raise UserError(
                self.env._(
                    "Melhor Envio returned an unreadable answer (HTTP %(code)s).",
                    code=response.status_code,
                )
            ) from error
        if response.status_code >= 400:
            message = data.get("message") if isinstance(data, dict) else False
            raise UserError(
                self.env._(
                    "Melhor Envio error (HTTP %(code)s): %(message)s",
                    code=response.status_code,
                    message=message or data,
                )
            )
        return data

    def action_sync_services(self):
        """Create or update one delivery method per Melhor Envio service, so
        each one can be offered (and quoted) on its own."""
        self.ensure_one()
        services = self._request(
            "GET", "/api/v2/me/shipment/services", authenticated=False
        )
        if not services:
            raise UserError(self.env._("Melhor Envio returned no shipping service."))
        carriers = self.env["delivery.carrier"].with_context(active_test=False)
        product = self.env.ref(
            "l10n_br_delivery_melhorenvio.product_product_delivery_melhorenvio"
        )
        for service in services:
            company_name = (service.get("company") or {}).get("name") or ""
            values = {
                "melhorenvio_service_id": service["id"],
                "melhorenvio_service_name": service.get("name"),
                "melhorenvio_company_name": company_name,
            }
            existing = carriers.search(
                [
                    ("melhorenvio_account_id", "=", self.id),
                    ("melhorenvio_service_id", "=", service["id"]),
                ],
                limit=1,
            )
            if existing:
                existing.write(values)
                continue
            carriers.create(
                {
                    **values,
                    "name": f"{company_name} {service.get('name') or ''}".strip(),
                    "delivery_type": "melhorenvio",
                    "integration_level": "rate",
                    "melhorenvio_account_id": self.id,
                    "product_id": product.id,
                    "company_id": self.company_id.id,
                }
            )
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Melhor Envio Services"),
            "res_model": "delivery.carrier",
            "view_mode": "list,form",
            "domain": [("melhorenvio_account_id", "=", self.id)],
            "context": {"active_test": False},
        }
