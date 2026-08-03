# Copyright 2026 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
import gzip
import logging
from dataclasses import dataclass

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

_logger = logging.getLogger(__name__)


@dataclass
class AdnResponse:
    """Normalized ADN response: HTTP status plus decoded JSON body."""

    status_code: int
    body: dict | None
    content: bytes


class AdnRestClient:
    """REST/mTLS client for the Sefin Nacional contributor API."""

    def __init__(self, base_url, client_cert_pem, client_key_pem=None, timeout=30):
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._session = requests.Session()
        self._session.cert = (
            (client_cert_pem, client_key_pem) if client_key_pem else client_cert_pem
        )
        self._session.verify = True
        retry = Retry(
            total=2,
            backoff_factor=0.5,
            status_forcelist=(502, 503, 504),
            allowed_methods=frozenset(["GET"]),
        )
        self._session.mount("https://", HTTPAdapter(max_retries=retry))

    @staticmethod
    def pack_dps(signed_xml):
        """gzip + base64 a signed DPS XML for the JSON request body."""
        if isinstance(signed_xml, str):
            signed_xml = signed_xml.encode("utf-8")
        return base64.b64encode(gzip.compress(signed_xml)).decode("ascii")

    def post_dps(self, gzip_b64_dps):
        """POST /nfse — submit a DPS and get the synchronous NFS-e response."""
        payload = {"dpsXmlGZipB64": gzip_b64_dps}
        resp = self._session.post(
            f"{self._base_url}/nfse", json=payload, timeout=self._timeout
        )
        return self._wrap(resp)

    def get_nfse(self, chave):
        """GET /nfse/{chave} — fetch an NFS-e (used to reconcile a lost POST)."""
        resp = self._session.get(
            f"{self._base_url}/nfse/{chave}", timeout=self._timeout
        )
        return self._wrap(resp)

    def get_dps(self, dps_id):
        """GET /dps/{id} — resolve the NFS-e key from a DPS id (reconcile)."""
        resp = self._session.get(
            f"{self._base_url}/dps/{dps_id}", timeout=self._timeout
        )
        return self._wrap(resp)

    def post_event(self, chave, gzip_b64):
        """POST /nfse/{chave}/eventos — register an event (e.g. cancellation)."""
        payload = {"pedidoRegistroEventoXmlGZipB64": gzip_b64}
        resp = self._session.post(
            f"{self._base_url}/nfse/{chave}/eventos",
            json=payload,
            timeout=self._timeout,
        )
        return self._wrap(resp)

    def get_event(self, chave, tipo_evento, num_seq):
        """GET /nfse/{chave}/eventos/{tipoEvento}/{numSeqEvento} — fetch one event."""
        resp = self._session.get(
            f"{self._base_url}/nfse/{chave}/eventos/{tipo_evento}/{num_seq}",
            timeout=self._timeout,
        )
        return self._wrap(resp)

    @staticmethod
    def _wrap(resp):
        try:
            body = resp.json()
        except ValueError:
            body = None
        _logger.debug("ADN response status=%s", resp.status_code)
        return AdnResponse(
            status_code=resp.status_code, body=body, content=resp.content
        )
