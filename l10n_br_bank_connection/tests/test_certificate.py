# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64
from datetime import datetime, timedelta

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.x509.oid import NameOID

from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged

from .common import ConnectionCommon
from .fake_bank import FAKE_MTLS, reset_state


def _pfx(common_name, password="segredo"):
    """A .pfx (base64, as uploaded) and its PEM certificate."""
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, common_name)])
    now = datetime.utcnow()
    cert = (
        x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(name)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - timedelta(days=1))
        .not_valid_after(now + timedelta(days=30))
        .sign(key, hashes.SHA256())
    )
    bundle = pkcs12.serialize_key_and_certificates(
        b"a1", key, cert, None, serialization.BestAvailableEncryption(password.encode())
    )
    return base64.b64encode(bundle), cert.public_bytes(serialization.Encoding.PEM)


@tagged("post_install", "-at_install")
class TestConnectionCertificate(ConnectionCommon, TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._setup_connection()

    def setUp(self):
        super().setUp()
        reset_state()

    def _mtls_connection(self, **values):
        return self._create_connection(adapter=FAKE_MTLS, client_secret=False, **values)

    def test_pfx_becomes_the_pem_fields(self):
        pfx, pem = _pfx("EMPRESA:91300766000147")
        connection = self._mtls_connection(
            certificate_pfx=pfx, certificate_pfx_password="segredo"
        )
        self.assertEqual(base64.b64decode(connection.certificate), pem)
        self.assertIn(b"PRIVATE KEY", base64.b64decode(connection.private_key))
        # Neither the file nor its password is kept.
        self.assertFalse(connection.certificate_pfx)
        self.assertFalse(connection.certificate_pfx_password)
        _adapter_class, config = connection._l10n_br_bank_prepare_adapter()
        self.assertEqual(config.certificado_pem, pem)

    def test_wrong_password_is_refused(self):
        pfx, _pem = _pfx("EMPRESA")
        with self.assertRaisesRegex(UserError, "password"):
            self._mtls_connection(certificate_pfx=pfx, certificate_pfx_password="x")

    def test_new_certificate_asks_to_renew_the_bank_credential(self):
        pfx, _pem = _pfx("PRIMEIRO")
        connection = self._mtls_connection(
            certificate_pfx=pfx, certificate_pfx_password="segredo"
        )
        self.assertTrue(connection.certificate_registered_fingerprint)
        self.assertFalse(connection.certificate_renewal_needed)
        pfx, _pem = _pfx("RENOVADO")
        connection.write(
            {"certificate_pfx": pfx, "certificate_pfx_password": "segredo"}
        )
        self.assertTrue(connection.certificate_renewal_needed)
        connection.action_certificate_renewed_at_bank()
        self.assertFalse(connection.certificate_renewal_needed)
        # A new environment comes with a new credential: no warning.
        pfx, _pem = _pfx("OUTRO")
        connection.write(
            {
                "certificate_pfx": pfx,
                "certificate_pfx_password": "segredo",
                "environment": "prod",
            }
        )
        self.assertFalse(connection.certificate_renewal_needed)

    def test_test_certificate_only_in_the_test_environment(self):
        connection = self._mtls_connection(name="Bradesco Teste")
        with self.assertRaisesRegex(UserError, "no certificate"):
            connection.action_download_certificate_pem()
        result = connection.action_generate_test_certificate()
        self.assertEqual(result["tag"], "display_notification")
        # Downloading is its own action: only the public part, never the key.
        action = connection.action_download_certificate_pem()
        cert = x509.load_pem_x509_certificate(base64.b64decode(connection.certificate))
        names = {attr.oid: attr.value for attr in cert.subject}
        self.assertTrue(names[NameOID.COMMON_NAME].endswith(":91300766000147"))
        self.assertEqual(names[NameOID.COUNTRY_NAME], "BR")
        self.assertIn(names[NameOID.ORGANIZATION_NAME], names[NameOID.COMMON_NAME])
        self.assertEqual(cert.signature_hash_algorithm.name, "sha256")
        self.assertEqual(cert.public_key().key_size, 2048)
        self.assertIn(f"{connection._name}/{connection.id}/certificate", action["url"])
        self.assertIn("download=true", action["url"])
        # The form reads binaries with bin_size: the size, not the content.
        connection.invalidate_recordset()
        on_form = connection.with_context(bin_size=True)
        self.assertTrue(on_form.certificate_fingerprint)
        self.assertFalse(on_form.certificate_renewal_needed)
        connection.environment = "prod"
        with self.assertRaises(UserError):
            connection.action_generate_test_certificate()
