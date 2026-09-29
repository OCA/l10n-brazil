# Copyright 2026 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import json
import logging
from datetime import datetime, timedelta, timezone

import requests

from odoo import _, fields, models
from odoo.exceptions import UserError

from ..constants import DEFAULT_CONSULT_PATH

_logger = logging.getLogger(__name__)


class DereReceitaIntegra(models.AbstractModel):
    _name = "l10n_br_dere.receita.integra"
    _description = "Receita Integra client for DeRE"

    def _token_param_key(self, company):
        return f"l10n_br_dere.token.{company.id}"

    def _clear_token(self, company):
        self.env["ir.config_parameter"].sudo().set_param(
            self._token_param_key(company), False
        )

    def _cached_token(self, company):
        raw = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param(self._token_param_key(company))
        )
        if not raw:
            return False
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            return False
        expires = fields.Datetime.to_datetime(payload.get("expires"))
        if not expires or expires <= fields.Datetime.now():
            return False
        return payload.get("token")

    def _store_token(self, company, token, expires):
        self.env["ir.config_parameter"].sudo().set_param(
            self._token_param_key(company),
            json.dumps(
                {
                    "token": token,
                    "expires": fields.Datetime.to_string(expires),
                }
            ),
        )

    def _request_token(self, company):
        company = company.sudo()
        if not company.dere_client_id or not company.dere_client_secret:
            raise UserError(
                _("Configure the Receita Integra client id and secret on the company.")
            )
        response = requests.post(
            company.dere_token_url,
            data={"grant_type": "client_credentials"},
            auth=(company.dere_client_id, company.dere_client_secret),
            timeout=60,
        )
        if response.status_code >= 400:
            raise UserError(
                _("Receita Integra token error %(code)s: %(body)s")
                % {"code": response.status_code, "body": response.text}
            )
        payload = response.json()
        token = payload.get("access_token")
        expires_in = int(payload.get("expires_in") or 3600)
        expires = fields.Datetime.now() + timedelta(seconds=max(expires_in - 60, 30))
        self._store_token(company, token, expires)
        return token

    def _get_token(self, company, force=False):
        if not force:
            cached = self._cached_token(company)
            if cached:
                return cached
        return self._request_token(company)

    def _authorized_request(self, company, method, url, **kwargs):
        headers = dict(kwargs.pop("headers", {}) or {})
        last = None
        for attempt in range(2):
            token = self._get_token(company, force=bool(attempt))
            headers["Authorization"] = f"Bearer {token}"
            last = getattr(requests, method)(url, headers=headers, **kwargs)
            if last.status_code != 401 or attempt:
                return last
            self._clear_token(company)
        return last

    def send_batch(self, company, xml_content):
        url = company._dere_batch_url()
        response = self._authorized_request(
            company,
            "post",
            url,
            data=xml_content.encode("utf-8"),
            headers={"Content-Type": "application/xml"},
            timeout=120,
        )
        return {
            "status_code": response.status_code,
            "text": response.text,
            "ok": 200 <= response.status_code < 300,
            "sent_at": datetime.now(timezone.utc),
        }

    def consult_batch(self, company, protocol):
        path = company.dere_consult_path or DEFAULT_CONSULT_PATH
        url = company._dere_api_base_url() + path.format(protocol=protocol)
        response = self._authorized_request(
            company,
            "get",
            url,
            headers={"Accept": "application/xml"},
            timeout=120,
        )
        return {
            "status_code": response.status_code,
            "text": response.text,
            "ok": 200 <= response.status_code < 300,
            "sent_at": datetime.now(timezone.utc),
        }
