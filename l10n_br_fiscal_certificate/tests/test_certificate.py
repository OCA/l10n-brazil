# Copyright 2019 Akretion - Renato Lima <renato.lima@akretion.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import timedelta

from erpbrasil.assinatura import misc

from odoo import Command, fields
from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase


class TestCertificate(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company_model = cls.env["res.company"]
        cls.certificate_model = cls.env["certificate.certificate"]
        cls.company = cls._create_compay()
        cls._switch_user_company(cls.env.user, cls.company)

        cls.cert_country = "BR"
        cls.cert_issuer_a = "EMISSOR A TESTE"
        cls.cert_issuer_b = "EMISSOR B TESTE"
        cls.cert_subject_valid = "CERTIFICADO VALIDO TESTE"
        cls.cert_date_exp = fields.Datetime.today() + timedelta(days=365)
        cls.cert_subject_invalid = "CERTIFICADO INVALIDO TESTE"
        cls.cert_passwd = "123456"

        cls.certificate_valid = misc.create_fake_certificate_file(
            valid=True,
            passwd=cls.cert_passwd,
            issuer=cls.cert_issuer_a,
            country=cls.cert_country,
            subject=cls.cert_subject_valid,
        )
        cls.certificate_invalid = misc.create_fake_certificate_file(
            valid=False,
            passwd=cls.cert_passwd,
            issuer=cls.cert_issuer_b,
            country=cls.cert_country,
            subject=cls.cert_subject_invalid,
        )

    @classmethod
    def _create_compay(cls):
        """Creating a company"""
        company = cls.env["res.company"].create(
            {
                "name": "Company Test Fiscal BR",
                "vat": "42.245.642/0001-09",
                "country_id": cls.env.ref("base.br").id,
                "state_id": cls.env.ref("base.state_br_sp").id,
            }
        )
        return company

    @classmethod
    def _switch_user_company(cls, user, company):
        """Add a company to the user's allowed & set to current."""
        user.write(
            {
                "company_ids": [Command.set((company + user.company_ids).ids)],
                "company_id": company.id,
            }
        )

    def _certificate_vals(self, cert_file, cert_type="nf-e", passwd=None):
        return {
            "type": cert_type,
            "subtype": "a1",
            "scope": "l10n_br",
            "pkcs12_password": passwd or self.cert_passwd,
            "content": cert_file,
            "company_id": self.company.id,
        }

    def test_valid_certificate(self):
        """Create and check a valid certificate"""
        cert = self.certificate_model.create(
            self._certificate_vals(self.certificate_valid)
        )

        self.assertEqual(cert.issuer_name, self.cert_issuer_a)
        self.assertEqual(cert.subject_common_name, self.cert_subject_valid)
        self.assertEqual(cert.date_end.year, self.cert_date_exp.year)
        self.assertEqual(cert.date_end.month, self.cert_date_exp.month)
        self.assertEqual(cert.date_end.day, self.cert_date_exp.day)
        self.assertEqual(cert.is_valid, True)
        self.assertEqual(cert.owner_cnpj_cpf, "")
        self.assertTrue(
            cert.name.startswith("NF-E - A1 - CERTIFICADO VALIDO TESTE - Valid:")
        )
        # Test method write
        cert.type = "e-cnpj"

    def test_certificate_wrong_password(self):
        """Write a valid certificate with wrong password"""
        with self.assertRaises(ValidationError):
            self.certificate_model.create(
                self._certificate_vals(self.certificate_valid, passwd="INVALID")
            )

    def test_invalid_certificate(self):
        """Create and check an expired certificate is flagged as invalid"""
        cert = self.certificate_model.create(
            self._certificate_vals(self.certificate_invalid)
        )
        self.assertFalse(cert.is_valid)

    def test_compute_field_and_method_to_get_certificate(self):
        """Test compute field and Method to get Certificate or e-CNPJ or e-NFe"""
        company = self.env.company
        with self.assertRaises(ValidationError):
            assert company.certificate
        cert = self.certificate_model.create(
            self._certificate_vals(self.certificate_valid)
        )

        company.certificate_nfe_id = cert
        assert company.certificate

        # Case where only e-CNPJ applies
        with self.assertRaises(ValidationError):
            assert company._get_br_ecertificate(only_ecnpj=True)
        company.certificate_nfe_id = False
        cert_ecnpj = self.certificate_model.create(
            self._certificate_vals(self.certificate_valid, cert_type="e-cnpj")
        )
        company.certificate_ecnpj_id = cert_ecnpj
        assert company._get_br_ecertificate(only_ecnpj=True)
