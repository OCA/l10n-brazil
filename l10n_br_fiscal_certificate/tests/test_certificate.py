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

    def _certificate_vals(self, cert_file, passwd=None, company=None):
        return {
            "scope": "l10n_br",
            "pkcs12_password": passwd or self.cert_passwd,
            "content": cert_file,
            "company_id": (company or self.company).id,
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
        self.assertTrue(cert.name.startswith("CERTIFICADO VALIDO TESTE - Valid:"))

    def test_default_scope(self):
        """The certificates of a Brazilian company are fiscal certificates"""
        vals = self._certificate_vals(self.certificate_valid)
        del vals["scope"]
        cert = self.certificate_model.create(vals)
        self.assertEqual(cert.scope, "l10n_br")

        other_company = self.company_model.create(
            {"name": "Company Test US", "country_id": self.env.ref("base.us").id}
        )
        vals["company_id"] = other_company.id
        cert = self.certificate_model.with_company(other_company).create(vals)
        self.assertFalse(cert.scope)

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

    def test_company_certificate(self):
        """The certificate set in the company is used"""
        company = self.env.company
        self.assertFalse(company.certificate)
        with self.assertRaises(ValidationError):
            company._get_br_ecertificate()

        cert = self.certificate_model.create(
            self._certificate_vals(self.certificate_valid)
        )
        company.certificate_id = cert
        self.assertEqual(company.certificate, cert)
        self.assertEqual(company._get_br_certificate(), cert)
        self.assertTrue(company._get_br_ecertificate())

    def test_company_certificate_expired(self):
        """An expired certificate can't be used"""
        company = self.env.company
        company.certificate_id = self.certificate_model.create(
            self._certificate_vals(self.certificate_invalid)
        )
        with self.assertRaises(ValidationError):
            company._get_br_ecertificate()

    def test_branch_uses_parent_certificate(self):
        """A branch without certificate uses the one of its parent company"""
        parent_cert = self.certificate_model.create(
            self._certificate_vals(self.certificate_valid)
        )
        self.company.certificate_id = parent_cert
        branch = self.company_model.create(
            {"name": "Branch Test Fiscal BR", "parent_id": self.company.id}
        )
        self.assertEqual(branch.certificate, parent_cert)
        self.assertTrue(branch._get_br_ecertificate())

        branch_cert = self.certificate_model.create(
            self._certificate_vals(self.certificate_valid, company=branch)
        )
        branch.certificate_id = branch_cert
        self.assertEqual(branch.certificate, branch_cert)
        # The parent company doesn't use the certificate of its branch
        self.assertEqual(self.company.certificate, parent_cert)

    def test_only_ecnpj(self):
        """Only a certificate issued to a CNPJ is used when only_ecnpj is set"""
        company = self.env.company
        company.certificate_id = self.certificate_model.create(
            self._certificate_vals(self.certificate_valid)
        )
        self.assertTrue(company._get_br_ecertificate())
        with self.assertRaises(ValidationError):
            company._get_br_ecertificate(only_ecnpj=True)

        company.certificate_id = self.certificate_model.create(
            self._certificate_vals(
                misc.create_fake_certificate_file(
                    valid=True,
                    passwd=self.cert_passwd,
                    issuer=self.cert_issuer_a,
                    country=self.cert_country,
                    subject="COMPANY TEST FISCAL BR:42245642000109",
                )
            )
        )
        self.assertEqual(company.certificate.owner_cnpj_cpf, "42245642000109")
        self.assertTrue(company._get_br_ecertificate(only_ecnpj=True))
