# Copyright 2026 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging
from datetime import datetime, timedelta, timezone

import requests

from odoo import _, models
from odoo.exceptions import UserError

from ..constants import (
    DOWNLOAD_TIMEOUT,
    ENVIRONMENT_PATH,
    REQUEST_TIMEOUT,
    SERVICE_PATH,
    STATUS_PATH,
)

_logger = logging.getLogger(__name__)

# Tokens are valid for one hour. Caching them in memory avoids one extra round
# trip per call; each worker keeps its own entry.
_TOKEN_CACHE: dict[tuple[str, int], tuple[str, datetime]] = {}


class ReceitaIntegraRtc(models.AbstractModel):
    _name = "l10n_br_cbs_assessment.client"
    _description = "Receita Integra client for the CBS assessment APIs"

    def _get_token(self, company):
        cache_key = (self.env.cr.dbname, company.id)
        cached = _TOKEN_CACHE.get(cache_key)
        now = datetime.now(timezone.utc)
        if cached and cached[1] > now:
            return cached[0]
        if not company.cbs_assessment_client_id or not (
            company.cbs_assessment_client_secret
        ):
            raise UserError(
                _(
                    "Configure the Receita Integra client id and secret of %s "
                    "before requesting the assessment.",
                    company.display_name,
                )
            )
        response = requests.post(
            company.cbs_assessment_token_url,
            auth=(
                company.cbs_assessment_client_id,
                company.cbs_assessment_client_secret,
            ),
            data={"grant_type": "client_credentials"},
            timeout=REQUEST_TIMEOUT,
        )
        if response.status_code >= 400:
            raise UserError(
                _(
                    "Receita Integra token error %(code)s: %(body)s",
                    code=response.status_code,
                    body=response.text,
                )
            )
        payload = response.json()
        token = payload.get("access_token")
        expires_in = int(payload.get("expires_in") or 3600)
        _TOKEN_CACHE[cache_key] = (
            token,
            now + timedelta(seconds=max(expires_in - 60, 30)),
        )
        return token

    def _base_url(self, company):
        return (company.cbs_assessment_api_url or "").rstrip("/") + ENVIRONMENT_PATH[
            company.cbs_assessment_environment
        ]

    def _open_request(self, company, service, return_url):
        """Open an asynchronous request and return the parsed answer."""
        path = SERVICE_PATH.get(service)
        if not path:
            raise UserError(
                _("Service %s is not served by the CBS assessment APIs.", service)
            )
        cnpj = company._assessment_cnpj_root()
        if len(cnpj) != 8:
            raise UserError(
                _(
                    "The CNPJ of %s does not provide the 8 digit root the "
                    "assessment endpoints require.",
                    company.display_name,
                )
            )
        url = f"{self._base_url(company)}/{path}/{cnpj}"
        response = requests.post(
            url,
            json={"urlRetorno": return_url},
            headers=self._headers(company),
            timeout=REQUEST_TIMEOUT,
        )
        return self._parse_response(response)

    def _get_status(self, company, ticket):
        url = f"{self._base_url(company)}/{STATUS_PATH}/{ticket}"
        response = requests.get(
            url,
            headers=self._headers(company),
            timeout=REQUEST_TIMEOUT,
        )
        return self._parse_response(response)

    def _download(self, signed_url):
        """Download the assessment file from the pre-signed URL.

        No authorization header is sent, because the signature already carries
        the authorisation and an extra header would invalidate it.
        """
        response = requests.get(signed_url, timeout=DOWNLOAD_TIMEOUT)
        if response.status_code >= 400:
            raise UserError(
                _(
                    "The assessment download failed with HTTP %(code)s: %(body)s",
                    code=response.status_code,
                    body=response.text[:500],
                )
            )
        return response.text

    def _headers(self, company):
        return {
            "Authorization": f"Bearer {self._get_token(company)}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def _parse_response(self, response):
        try:
            payload = response.json()
        except ValueError:
            payload = {
                "codigoErro": str(response.status_code),
                "mensagemErro": response.text[:500],
            }
        if response.status_code >= 400 and not payload.get("codigoErro"):
            payload = dict(
                payload,
                codigoErro=str(response.status_code),
                mensagemErro=response.text[:500],
            )
        return payload
