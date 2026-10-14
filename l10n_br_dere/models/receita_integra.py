# Copyright 2026 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging
from datetime import datetime, timedelta, timezone

import requests

from odoo import _, fields, models
from odoo.exceptions import UserError

from ..constants import DEFAULT_CONSULT_PATH, TOKEN_REFRESH_MIN_MINUTES

_logger = logging.getLogger(__name__)


class DereReceitaIntegra(models.AbstractModel):
    _name = "l10n_br_dere.receita.integra"
    _description = "Receita Integra client for DeRE"

    def _token_record(self, company):
        company = company.sudo()
        return self.env["l10n_br_dere.token"]._lock(company.dere_client_id)

    def _clear_token(self, company):
        company = company.sudo()
        if not company.dere_client_id:
            return
        record = (
            self.env["l10n_br_dere.token"]
            .sudo()
            .search(
                [("client_id", "=", company.dere_client_id)],
                limit=1,
            )
        )
        if record:
            record.write({"access_token": False, "expires_at": False})

    def _token_age(self, company):
        company = company.sudo()
        record = (
            self.env["l10n_br_dere.token"]
            .sudo()
            .search(
                [("client_id", "=", company.dere_client_id)],
                limit=1,
            )
        )
        if not record or not record.issued_at:
            return timedelta.max
        return fields.Datetime.now() - record.issued_at

    def _request_token(self, company, record):
        company = company.sudo()
        if not company.dere_client_id or not company.dere_client_secret:
            raise UserError(
                _("Configure the Receita Integra client id and secret on the company.")
            )
        now = fields.Datetime.now()
        recent = record._assert_can_emit(now)
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
        expires = now + timedelta(seconds=max(expires_in - 60, 30))
        record.write(
            {
                "access_token": token,
                "expires_at": expires,
                "issued_at": now,
            }
        )
        record._remember_emission(now, recent)
        return token

    def _get_token(self, company, force=False):
        company = company.sudo()
        if not company.dere_client_id or not company.dere_client_secret:
            raise UserError(
                _("Configure the Receita Integra client id and secret on the company.")
            )
        record = self._token_record(company)
        now = fields.Datetime.now()
        if (
            not force
            and record.access_token
            and record.expires_at
            and record.expires_at > now
        ):
            return record.access_token
        return self._request_token(company, record)

    def _authorized_request(self, company, method, url, **kwargs):
        headers = dict(kwargs.pop("headers", {}) or {})
        last = None
        for attempt in range(2):
            token = self._get_token(company, force=bool(attempt))
            headers["Authorization"] = f"Bearer {token}"
            last = getattr(requests, method)(url, headers=headers, **kwargs)
            if last.status_code != 401 or attempt:
                return last
            if self._token_age(company) < timedelta(minutes=TOKEN_REFRESH_MIN_MINUTES):
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
