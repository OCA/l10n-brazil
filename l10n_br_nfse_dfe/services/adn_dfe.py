# Copyright 2026 Escodoo - Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging
from dataclasses import dataclass

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

_logger = logging.getLogger(__name__)


@dataclass
class AdnDfeResponse:
    """Normalized ADN distribution response."""

    status_code: int
    body: dict | None
    content: bytes
    headers: dict
    text: str

    @property
    def ok(self):
        return 200 <= self.status_code < 300


class AdnDfeClient:
    """REST/mTLS client for the NFS-e ADN distribution API.

    This is the tomador feed (``GET /contribuintes/DFe/{NSU}``). It is not
    the Sefin Nacional emission API used to authorize a DPS.
    """

    def __init__(self, base_url, client_cert_pem, timeout=30):
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._session = requests.Session()
        self._session.cert = client_cert_pem
        self._session.verify = True
        self._session.headers["Accept"] = "application/json"
        retry = Retry(
            total=2,
            backoff_factor=0.5,
            status_forcelist=(502, 503, 504),
            allowed_methods=frozenset(["GET"]),
        )
        self._session.mount("https://", HTTPAdapter(max_retries=retry))

    def get(self, path, params=None):
        url = f"{self._base_url}{path}"
        resp = self._session.get(url, params=params, timeout=self._timeout)
        return self._wrap(resp)

    @staticmethod
    def _wrap(resp):
        try:
            body = resp.json()
        except ValueError:
            body = None
        if not isinstance(body, dict):
            body = None
        _logger.debug("ADN DFe response status=%s", resp.status_code)
        return AdnDfeResponse(
            status_code=resp.status_code,
            body=body,
            content=resp.content or b"",
            headers=dict(resp.headers or {}),
            text=resp.text or "",
        )
