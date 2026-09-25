# Copyright (C) 2026 - TODAY, Kaynnan Lemes <kaynnan.lemes@escodoo.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import logging
import time

import requests
from erpbrasil.assinatura.certificado import ArquivoCertificado

from odoo import _
from odoo.exceptions import UserError

from ..constants.duimp import (
    DUIMP_API_PATH_PREFIX,
    DUIMP_AUTH_PATH,
    DUIMP_DEFAULT_VERSION,
    DUIMP_ENVIRONMENT_VALIDATION,
    DUIMP_ENVIRONMENTS,
    DUIMP_ROLE_TYPE_DEFAULT,
    DUIMP_TOKEN_CACHE_SECONDS,
)

_logger = logging.getLogger(__name__)


class DuimpWebserviceError(UserError):
    """Raised when the Siscomex DUIMP webservice cannot be reached or
    returns an unexpected response."""


class DuimpInMemoryTokenStore:
    """In-process cache for the DUIMP auth token, shared by every
    ``DuimpWebservice`` instance created in this worker within
    ``DUIMP_TOKEN_CACHE_SECONDS``.

    Kept in plain process memory - not persisted to the database - on
    purpose: persisting it would need an explicit ``cr.commit()`` to
    survive a later rollback of the same request/transaction (e.g. the
    DUIMP being queried turns out not to exist), but committing the
    transaction by hand is against OCA guidelines
    (https://github.com/OCA/odoo-community.org/blob/master/website/Contribution/CONTRIBUTING.rst#never-commit-the-transaction)
    and is flagged by the ``invalid-commit`` pylint check. A token that
    is only cached in memory is simply not exposed to that problem.
    """

    _cache = {}

    def __init__(self, key):
        self.key = key

    def get(self):
        cached = self._cache.get(self.key)
        if not cached:
            return None
        token, csrf_token, obtained_at = cached
        if time.time() - obtained_at > DUIMP_TOKEN_CACHE_SECONDS:
            return None
        return token, csrf_token

    def set(self, token, csrf_token):
        self._cache[self.key] = (token, csrf_token, time.time())


class DuimpWebservice:
    """Lightweight REST client for the "Consulta aos Dados da Duimp" API
    of the Portal Único Siscomex (Import Declaration).

    Authentication follows the Portal Único standard: an SSL handshake is
    performed presenting an e-CPF (ICP-Brasil) digital certificate of the
    natural person responsible for the DUIMP (the IMPEXP profile used to
    query it rejects e-CNPJ certificates with HTTP 422 PLAT-ER2008), which
    yields a JWT (``Set-Token``) and a CSRF token (``X-CSRF-Token``) that
    must be sent on every subsequent call. The
    certificate is turned into temporary PEM files using
    ``erpbrasil.assinatura.certificado.ArquivoCertificado``, the same
    helper already used by ``erpbrasil.transmissao`` to authenticate the
    NFe/CTe/MDFe SOAP webservices in this localization.

    See ``odoo.addons.l10n_br_duimp.constants.duimp`` for the
    reference links used to derive the endpoints below.

    The Portal Único rejects a new authentication attempt if the same
    user authenticated less than 60 seconds ago (HTTP 422 PLAT-ER2033,
    confirmed live), so a fresh token must not be requested on every
    call. ``token_store``, if given, is a small object exposing
    ``get() -> (token, csrf_token) | None`` and ``set(token,
    csrf_token)`` used to persist and reuse the token across separate
    ``DuimpWebservice`` instances (see ``res.company._get_duimp_webservice``
    for the real, ``ir.config_parameter``-backed implementation).
    """

    def __init__(
        self,
        certificate,
        environment=DUIMP_ENVIRONMENT_VALIDATION,
        role_type=DUIMP_ROLE_TYPE_DEFAULT,
        token_store=None,
    ):
        self.certificate = certificate
        self.base_url = DUIMP_ENVIRONMENTS.get(
            environment, DUIMP_ENVIRONMENTS[DUIMP_ENVIRONMENT_VALIDATION]
        )
        self.role_type = role_type
        self.token_store = token_store
        self._token = None
        self._csrf_token = None
        if self.token_store:
            cached = self.token_store.get()
            if cached:
                self._token, self._csrf_token = cached

    def _request(self, method, path, **kwargs):
        with ArquivoCertificado(self.certificate, "w") as (key, cert):
            try:
                return requests.request(
                    method,
                    f"{self.base_url}{path}",
                    cert=(key, cert),
                    timeout=60,
                    **kwargs,
                )
            except requests.exceptions.RequestException as exc:
                raise DuimpWebserviceError(
                    _("Error connecting to the Portal Único Siscomex: %s") % exc
                ) from exc

    def _authenticate(self):
        response = self._request(
            "POST",
            DUIMP_AUTH_PATH,
            headers={"Role-Type": self.role_type},
        )
        if response.status_code != 200:
            if "PLAT-ER2033" in response.text:
                raise DuimpWebserviceError(
                    _(
                        "The Portal Único Siscomex rejected a new login because "
                        "this same e-CPF certificate authenticated less than 60 "
                        "seconds ago (this happens if someone also logged in "
                        "directly at portalunico.siscomex.gov.br around the same "
                        "time). Please wait about a minute and try again."
                    )
                )
            raise DuimpWebserviceError(
                _(
                    "Authentication to the Portal Único Siscomex failed "
                    "(HTTP %(status)s): %(body)s"
                )
                % {"status": response.status_code, "body": response.text}
            )
        self._token = response.headers.get("Set-Token")
        self._csrf_token = response.headers.get("X-CSRF-Token")
        if not self._token or not self._csrf_token:
            raise DuimpWebserviceError(
                _(
                    "Authentication to the Portal Único Siscomex did not "
                    "return the expected Set-Token/X-CSRF-Token headers."
                )
            )
        if self.token_store:
            self.token_store.set(self._token, self._csrf_token)

    def _auth_headers(self):
        if not self._token:
            self._authenticate()
        return {
            "Authorization": self._token,
            "X-CSRF-Token": self._csrf_token,
        }

    def _get(self, path, params=None, not_found_returns_empty=False, _retry=True):
        response = self._request(
            "GET", path, headers=self._auth_headers(), params=params
        )
        if response.status_code == 401 and _retry:
            # The cached/reused token turned out to be stale: drop it and
            # authenticate again, once, instead of failing outright.
            self._token = None
            self._csrf_token = None
            return self._get(
                path,
                params=params,
                not_found_returns_empty=not_found_returns_empty,
                _retry=False,
            )
        if response.status_code == 404:
            if not_found_returns_empty:
                return []
            raise DuimpWebserviceError(
                _("DUIMP not found in the Portal Único Siscomex (%s).") % path
            )
        if response.status_code not in (200, 206):
            raise DuimpWebserviceError(
                _(
                    "Unexpected response from the Portal Único Siscomex "
                    "(HTTP %(status)s): %(body)s"
                )
                % {"status": response.status_code, "body": response.text}
            )
        return response.json()

    def get_general_data(self, duimp_number, duimp_version=None):
        """GET {DUIMP_API_PATH_PREFIX}/{numeroDuimp}/{versaoDuimp}

        Returns the general data of the DUIMP: identification, status,
        cargo, additions, tributes (federal taxes already calculated),
        payments, etc.
        """
        path = (
            f"{DUIMP_API_PATH_PREFIX}/{duimp_number}"
            f"/{duimp_version or DUIMP_DEFAULT_VERSION}"
        )
        return self._get(path)

    def get_items(self, duimp_number, duimp_version=None, offset=0, limit=500):
        """GET {DUIMP_API_PATH_PREFIX}/{numeroDuimp}/{versaoDuimp}/itens

        Returns the paginated list of merchandise items of the DUIMP,
        each one with its own tax calculation breakdown
        (``itemTributo.calculosTributos``).
        """
        path = (
            f"{DUIMP_API_PATH_PREFIX}/{duimp_number}"
            f"/{duimp_version or DUIMP_DEFAULT_VERSION}/itens"
        )
        result = self._get(path, params={"offset": offset, "limit": limit})
        if isinstance(result, dict):
            return result.get("itens") or result.get("content") or []
        return result

    def search_access_keys_by_importer(
        self, importer_ni, date_from, date_to, offset=0, limit=100
    ):
        """GET {DUIMP_API_PATH_PREFIX}/chaves-acesso/importadores/{niImportador}

        Lists every DUIMP registered for the given importer (company
        CNPJ) within the date range, without requiring the DUIMP number
        to be known upfront. Returns a list of
        ``{"numero": ..., "chaveAcesso": ...}``. A 404 here means no
        DUIMP was registered for this importer/date range (confirmed
        live: the same status code the single-DUIMP lookups use for a
        genuine "not found"), so it is treated as an empty result
        instead of raising.
        """
        path = f"{DUIMP_API_PATH_PREFIX}/chaves-acesso/importadores/{importer_ni}"
        result = self._get(
            path,
            params={
                "data-inicio": date_from,
                "data-termino": date_to,
                "offset": offset,
                "limit": limit,
            },
            not_found_returns_empty=True,
        )
        if isinstance(result, dict):
            return result.get("content") or []
        return result
