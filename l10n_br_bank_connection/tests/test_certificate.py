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


def _pkcs12(common_name, password=None):
    """A PKCS12 bundle (key and self-signed certificate) and its PEM certificate."""
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
    encryption = (
        serialization.BestAvailableEncryption(password.encode())
        if password
        else serialization.NoEncryption()
    )
    bundle = pkcs12.serialize_key_and_certificates(b"a1", key, cert, None, encryption)
    return bundle, cert.public_bytes(serialization.Encoding.PEM)


@tagged("post_install", "-at_install")
class TestConnectionCertificate(ConnectionCommon, TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._setup_connection()

    def setUp(self):
        super().setUp()
        reset_state()

    def _certificate(self, common_name="EMPRESA:91300766000147", password="segredo"):
        bundle, pem = _pkcs12(common_name, password)
        record = self.env["certificate.certificate"].create(
            {
                "name": common_name,
                "content": base64.b64encode(bundle),
                "pkcs12_password": password,
                "company_id": self.env.company.id,
            }
        )
        return record, pem

    def _mtls_connection(self, **values):
        return self._create_connection(adapter=FAKE_MTLS, client_secret=False, **values)

    def test_certificate_record_reaches_the_bank(self):
        record, pem = self._certificate()
        connection = self._mtls_connection(
            certificate=base64.b64encode(b"old pem"), certificate_id=record.id
        )
        self.assertTrue(connection.uses_certificate)
        # The prepared config carries the PEM of the record, not the binary field.
        _adapter_class, config = connection._l10n_br_bank_prepare_adapter()
        self.assertEqual(config.certificado_pem, pem)
        self.assertIn(b"PRIVATE KEY", config.chave_pem)

    def test_download_the_public_part_of_a_customer_a1(self):
        record, _pem = self._certificate("A1 DO CLIENTE")
        connection = self._mtls_connection(certificate_id=record.id)
        action = connection.action_download_certificate_pem()
        self.assertIn(
            f"certificate.certificate/{record.id}/pem_certificate", action["url"]
        )

    def test_pem_fields_without_a_certificate_record(self):
        _bundle, pem = _pkcs12("SEM REGISTRO")
        connection = self._mtls_connection(
            certificate=base64.b64encode(pem),
            private_key=base64.b64encode(b"-----BEGIN PRIVATE KEY-----"),
        )
        _adapter_class, config = connection._l10n_br_bank_prepare_adapter()
        self.assertEqual(config.certificado_pem, pem)

    def test_certificate_without_private_key_is_refused(self):
        _bundle, pem = _pkcs12("SO PUBLICO")
        record = self.env["certificate.certificate"].create(
            {"name": "so publico", "content": base64.b64encode(pem)}
        )
        # Refused on save, by the configuration check of the connection.
        with self.assertRaisesRegex(UserError, "no private key"):
            self._mtls_connection(certificate_id=record.id)

    def test_new_certificate_asks_to_renew_the_bank_credential(self):
        first, _pem = self._certificate("PRIMEIRO")
        connection = self._mtls_connection(certificate_id=first.id)
        self.assertTrue(connection.certificate_registered_fingerprint)
        self.assertFalse(connection.certificate_renewal_needed)
        renewed, _pem = self._certificate("RENOVADO")
        connection.certificate_id = renewed
        self.assertTrue(connection.certificate_renewal_needed)
        connection.action_certificate_renewed_at_bank()
        self.assertFalse(connection.certificate_renewal_needed)
        self.assertEqual(
            connection.certificate_registered_fingerprint,
            connection.certificate_fingerprint,
        )
        # A new environment comes with a new credential: no warning.
        other, _pem = self._certificate("OUTRO")
        connection.write({"certificate_id": other.id, "environment": "prod"})
        self.assertFalse(connection.certificate_renewal_needed)

    def test_test_certificate_only_in_the_test_environment(self):
        connection = self._mtls_connection(name="Bradesco Teste")
        with self.assertRaisesRegex(UserError, "no certificate"):
            connection.action_download_certificate_pem()
        result = connection.action_generate_test_certificate()
        self.assertEqual(result["tag"], "display_notification")
        record = connection.certificate_id
        self.assertTrue(record.private_key_id)
        self.assertTrue(record.pem_certificate)
        cert = x509.load_pem_x509_certificate(base64.b64decode(record.pem_certificate))
        names = {attr.oid: attr.value for attr in cert.subject}
        self.assertTrue(names[NameOID.COMMON_NAME].endswith(":91300766000147"))
        self.assertEqual(names[NameOID.COUNTRY_NAME], "BR")
        self.assertIn(names[NameOID.ORGANIZATION_NAME], names[NameOID.COMMON_NAME])
        self.assertEqual(cert.signature_hash_algorithm.name, "sha256")
        self.assertEqual(cert.public_key().key_size, 2048)
        # Downloading is its own action: only the public part, never the key.
        action = connection.action_download_certificate_pem()
        self.assertIn(
            f"certificate.certificate/{record.id}/pem_certificate", action["url"]
        )
        self.assertIn("download=true", action["url"])
        # The form reads binaries with bin_size: the size, not the content.
        connection.invalidate_recordset()
        on_form = connection.with_context(bin_size=True)
        self.assertEqual(
            on_form.certificate_fingerprint, connection.certificate_fingerprint
        )
        self.assertFalse(on_form.certificate_renewal_needed)
        # It goes to the bank as any certificate record.
        _adapter_class, config = connection._l10n_br_bank_prepare_adapter()
        self.assertEqual(
            config.certificado_pem, base64.b64decode(record.pem_certificate)
        )
        connection.environment = "prod"
        with self.assertRaises(UserError):
            connection.action_generate_test_certificate()
