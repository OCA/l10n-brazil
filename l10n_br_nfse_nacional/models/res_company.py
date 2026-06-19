# Copyright 2026 - TODAY, Kaynnan Lemes <kaynnan.lemes@escodoo.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
import logging
import tempfile

from odoo import fields, models

from ..constants.nfse_nacional import TIMEOUT

_logger = logging.getLogger(__name__)


class ResCompany(models.Model):
    _inherit = "res.company"

    provedor_nfse = fields.Selection(
        selection_add=[
            ("nfse_nacional", "NFS-e Nacional (SEFIN)"),
        ]
    )

    nfse_nacional_update_authorized_status = fields.Boolean(
        string="Include Authorized Documents in Status Check",
        help=(
            "If checked, authorized documents will be included in the status check "
            "cron. The system will verify the status with SEFIN and automatically "
            "update the status in Odoo if there are discrepancies."
        ),
        default=False,
    )

    nfse_nacional_force_odoo_danfse = fields.Boolean(
        string="Force Local DANFSE",
        help=(
            "If checked, always generate the DANFSE locally via brazilfiscalreport "
            "instead of downloading the PDF from the SEFIN DANFSE service."
        ),
        default=False,
    )

    def _get_sefin_session(self):
        """Build a requests.Session with mTLS using the company digital certificate.

        Extracts the PEM certificate and private key from the company's PKCS12
        certificate (obtained via _get_br_ecertificate) and configures the session
        for mutual TLS authentication with the SEFIN API.

        Returns:
            requests.Session: Session configured for SEFIN with client certificate.
        """
        import requests

        self.ensure_one()
        session = requests.Session()
        session.verify = self.nfse_ssl_verify

        try:
            ecert = self._get_br_ecertificate()
            pfx_data = base64.b64decode(ecert.arquivo)
            password = (ecert.senha or "").encode()

            from cryptography.hazmat.primitives.serialization import (
                Encoding,
                NoEncryption,
                PrivateFormat,
                pkcs12,
            )

            private_key, certificate, _ = pkcs12.load_key_and_certificates(
                pfx_data, password
            )

            cert_pem = certificate.public_bytes(Encoding.PEM)
            key_pem = private_key.private_bytes(
                Encoding.PEM, PrivateFormat.PKCS8, NoEncryption()
            )

            cert_file = tempfile.NamedTemporaryFile(
                suffix=".pem", delete=False, mode="wb"
            )
            cert_file.write(cert_pem)
            cert_file.flush()

            key_file = tempfile.NamedTemporaryFile(
                suffix=".pem", delete=False, mode="wb"
            )
            key_file.write(key_pem)
            key_file.flush()

            session.cert = (cert_file.name, key_file.name)

        except Exception as e:
            _logger.warning(
                "Could not configure mTLS for SEFIN session: %s. "
                "Proceeding without client certificate.",
                e,
            )

        session.headers.update(
            {
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
        )
        session.timeout = TIMEOUT
        return session
