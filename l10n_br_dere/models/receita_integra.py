# Copyright 2026 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

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

    def _get_token(self, company):
        now = fields.Datetime.now()
        cache = self.env.context.get("dere_token_cache") or {}
        key = company.id
        cached = cache.get(key)
        if cached and cached["expires"] > now:
            return cached["token"]
        if not company.dere_client_id or not company.dere_client_secret:
            raise UserError(
                _("Configure the Receita Integra client id and secret on the company.")
            )
        response = requests.post(
            company.dere_token_url,
            data={
                "grant_type": "client_credentials",
                "client_id": company.dere_client_id,
                "client_secret": company.dere_client_secret,
            },
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
        cache[key] = {
            "token": token,
            "expires": now + timedelta(seconds=max(expires_in - 60, 30)),
        }
        return token

    def send_batch(self, company, xml_content):
        token = self._get_token(company)
        url = (company.dere_api_url or "").rstrip("/") + (company.dere_api_path or "")
        response = requests.post(
            url,
            data=xml_content.encode("utf-8"),
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/xml",
            },
            timeout=120,
        )
        return {
            "status_code": response.status_code,
            "text": response.text,
            "ok": 200 <= response.status_code < 300,
            "sent_at": datetime.now(timezone.utc),
        }

    def consult_batch(self, company, protocol):
        token = self._get_token(company)
        path = company.dere_consult_path or DEFAULT_CONSULT_PATH
        url = (company.dere_api_url or "").rstrip("/") + path.format(protocol=protocol)
        response = requests.get(
            url,
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/xml",
            },
            timeout=120,
        )
        return {
            "status_code": response.status_code,
            "text": response.text,
            "ok": 200 <= response.status_code < 300,
            "sent_at": datetime.now(timezone.utc),
        }
