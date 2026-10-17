# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import base64
import json
import logging
import os
import stat
import tempfile

import requests

from odoo import _, api, models
from odoo.exceptions import UserError

from ..constants import (
    SERPRO_BASE_URL,
    SERPRO_SYSTEM_VERSION,
    SERPRO_TIMEOUT,
    SERPRO_TOKEN_URL,
    SERVICES,
)

_logger = logging.getLogger(__name__)


class IntegraContador(models.AbstractModel):
    """Transport for the Integra Contador API.

    Everything that touches the network lives here, so the assessment only
    knows business verbs. Two rules are load bearing:

    - the request is authenticated by the e-CNPJ certificate over mTLS, and
      the private key only ever exists in a file the process owns and deletes;
    - nothing sensitive is logged. Not the token, not the certificate, not the
      CNPJ of the taxpayer, not the payload. What goes to the log is the
      service and the record, which is enough to trace a call.
    """

    _name = "l10n_br_dctfweb.integra.contador"
    _description = "Integra Contador transport"

    # ------------------------------------------------------------------
    # Credentials
    # ------------------------------------------------------------------

    @api.model
    def _check_company_setup(self, company):
        company = company.sudo()
        if not company.serpro_environment:
            raise UserError(
                _("Set the Integra Contador environment of the company %s.")
                % company.display_name
            )
        if company.serpro_environment == "production":
            missing = not (
                company.serpro_consumer_key and company.serpro_consumer_secret
            )
            if missing:
                raise UserError(
                    _(
                        "The company %s has no Integra Contador consumer key "
                        "and secret. They are issued by the Serpro store."
                    )
                    % company.display_name
                )
        return company

    @api.model
    def _get_token(self, company):
        """Ask for a bearer token, or reuse the one the company still holds.

        The trial hands out a fixed demo token, published in the platform
        documentation: fill it in on the company and no credential is needed
        to develop against the trial.
        """
        company = self._check_company_setup(company)
        if company.serpro_access_token and not company._serpro_token_expired():
            return company.serpro_access_token
        if company.serpro_environment == "trial" and company.serpro_access_token:
            return company.serpro_access_token
        credentials = f"{company.serpro_consumer_key}:{company.serpro_consumer_secret}"
        basic = base64.b64encode(credentials.encode()).decode()
        try:
            with self._certificate_files(company) as certificate:
                response = requests.post(
                    SERPRO_TOKEN_URL[company.serpro_environment],
                    data={"grant_type": "client_credentials"},
                    headers={
                        "Authorization": "Basic %s" % basic,
                        "Content-Type": "application/x-www-form-urlencoded",
                    },
                    cert=certificate,
                    timeout=SERPRO_TIMEOUT,
                )
        except requests.exceptions.Timeout as exc:
            _logger.warning(
                "Integra Contador did not answer the token request in time",
                exc_info=True,
            )
            raise UserError(
                _("The Integra Contador did not answer the token request in time.")
            ) from exc
        except requests.exceptions.RequestException as exc:
            _logger.warning("Integra Contador token request failed", exc_info=True)
            raise UserError(_("The Integra Contador token request failed.")) from exc
        if response.status_code != 200:
            raise UserError(
                _("The Integra Contador refused the credentials (HTTP %s).")
                % response.status_code
            )
        payload = response.json()
        company._store_serpro_token(
            payload.get("access_token"), payload.get("expires_in")
        )
        return company.serpro_access_token

    # ------------------------------------------------------------------
    # Certificate
    # ------------------------------------------------------------------

    @api.model
    def _certificate_files(self, company):
        """Give the certificate and the key as a pair of temporary files.

        `requests` needs paths, and the A1 certificate lives in the database.
        The library ships a context manager for this, but it writes the two
        halves into swapped names, so the pair is built here: the key file is
        created with owner-only permission and removed on the way out, which
        is the whole point of doing it by hand.
        """
        return _CertificateFiles(company)

    # ------------------------------------------------------------------
    # Request
    # ------------------------------------------------------------------

    @api.model
    def _build_request(self, company, taxpayer_cnpj, service_key, data):
        """The envelope every service shares."""
        service = SERVICES[service_key]
        contractor = company.sudo()._serpro_contractor_cnpj()
        return {
            "contratante": {"numero": contractor, "tipo": 2},
            "autorPedidoDados": {
                "numero": company.sudo()._serpro_author_cnpj(),
                "tipo": 2,
            },
            "contribuinte": {"numero": taxpayer_cnpj, "tipo": 2},
            "pedidoDados": {
                "idSistema": service["system"],
                "idServico": service["service"],
                "versaoSistema": SERPRO_SYSTEM_VERSION,
                "dados": json.dumps(data, ensure_ascii=False),
            },
        }

    @api.model
    def call(self, company, taxpayer_cnpj, service_key, data, record=None):
        """Call one service and answer the parsed body.

        The caller gets the body and the status; deciding what a body means is
        business, and belongs to the assessment.
        """
        service = SERVICES[service_key]
        token = self._get_token(company)
        base = SERPRO_BASE_URL[company.sudo().serpro_environment]
        url = f"{base}/{service['endpoint']}"
        body = self._build_request(company, taxpayer_cnpj, service_key, data)
        _logger.info(
            "Integra Contador %s (%s) for %s",
            service["service"],
            service["endpoint"],
            record and record.display_name or "no record",
        )
        try:
            with self._certificate_files(company) as certificate:
                response = requests.post(
                    url,
                    json=body,
                    headers={
                        "Authorization": "Bearer %s" % token,
                        "jwt_token": company.sudo().serpro_jwt_token or "",
                        "Content-Type": "application/json",
                    },
                    cert=certificate,
                    timeout=SERPRO_TIMEOUT,
                )
        except requests.exceptions.Timeout as exc:
            _logger.warning(
                "Integra Contador %s timed out", service["service"], exc_info=True
            )
            raise UserError(
                _("The service %s did not answer in time.") % service["name"]
            ) from exc
        except requests.exceptions.RequestException as exc:
            _logger.warning(
                "Integra Contador %s failed", service["service"], exc_info=True
            )
            raise UserError(
                _("The call to the service %s failed.") % service["name"]
            ) from exc
        return self._parse(response, service)

    @api.model
    def _parse(self, response, service):
        """Turn the answer into a dict, keeping the authority's messages."""
        try:
            body = response.json()
        except ValueError:
            body = {}
        if response.status_code >= 400 and not body:
            raise UserError(
                _("The service %(name)s answered HTTP %(status)s.")
                % {"name": service["name"], "status": response.status_code}
            )
        # The platform nests the useful part in "dados" as a JSON string. Only
        # a structure is worth parsing: "12345" is a receipt number, and
        # json.loads would turn it into an integer nobody asked for.
        data = body.get("dados")
        if isinstance(data, str) and data:
            try:
                parsed = json.loads(data)
            except ValueError:
                parsed = None
            if isinstance(parsed, dict | list):
                body["dados"] = parsed
        body["_status_code"] = response.status_code
        return body

    @api.model
    def messages(self, body):
        """The authority's messages, flattened for a chatter line."""
        messages = body.get("mensagens") or []
        return "\n".join(
            f"{message.get('codigo', '')} {message.get('texto', '')}"
            for message in messages
            if isinstance(message, dict)
        )

    @api.model
    def succeeded(self, body):
        status = body.get("status") or body.get("_status_code")
        return str(status) in ("200", "201")


class _CertificateFiles:
    """Write the A1 pair to disk for the length of one request."""

    def __init__(self, company):
        self.company = company
        self.cert_path = None
        self.key_path = None

    def __enter__(self):
        certificate = self.company.sudo()._get_br_ecertificate(only_ecnpj=True)
        certificate_pem, key_pem = certificate.cert_chave()
        self.cert_path = self._write(certificate_pem)
        self.key_path = self._write(key_pem)
        return (self.cert_path, self.key_path)

    def _write(self, content):
        handle, path = tempfile.mkstemp(suffix=".pem")
        os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)
        with os.fdopen(handle, "w") as temporary:
            temporary.write(content)
        return path

    def __exit__(self, exception_type, exception_value, traceback):
        for path in (self.cert_path, self.key_path):
            if path and os.path.exists(path):
                os.remove(path)
        return False
