# Copyright 2019 Akretion - Renato Lima <renato.lima@akretion.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import timedelta

from odoo import fields
from odoo.exceptions import ValidationError
from odoo.tests import common
from odoo.tools.misc import format_date

from ..tools import misc


class TestCertificate(common.TransactionCase):
    def setUp(self):
        super().setUp()

        self.company_model = self.env["res.company"]
        self.certificate_model = self.env["l10n_br_fiscal.certificate"]
        self.company = self._create_compay()
        self._switch_user_company(self.env.user, self.company)

        self.cert_country = "BR"
        self.cert_issuer_a = "EMISSOR A TESTE"
        self.cert_issuer_b = "EMISSOR B TESTE"
        self.cert_subject_valid = "CERTIFICADO VALIDO TESTE"
        self.cert_date_exp = fields.Datetime.today() + timedelta(days=365)
        self.cert_subject_invalid = "CERTIFICADO INVALIDO TESTE"
        self.cert_passwd = "123456"
        self.cert_name = "{} - {} - {} - Valid: {}".format(
            "NF-E",
            "A1",
            self.cert_subject_valid,
            format_date(self.env, self.cert_date_exp),
        )

        self.certificate_valid = misc.create_fake_certificate_file(
            valid=True,
            passwd=self.cert_passwd,
            issuer=self.cert_issuer_a,
            country=self.cert_country,
            subject=self.cert_subject_valid,
        )
        self.certificate_invalid = misc.create_fake_certificate_file(
            valid=False,
            passwd=self.cert_passwd,
            issuer=self.cert_issuer_b,
            country=self.cert_country,
            subject=self.cert_subject_invalid,
        )

    def _create_compay(self):
        """Creating a company"""
        company = self.env["res.company"].create(
            {
                "name": "Company Test Fiscal BR",
                "cnpj_cpf": "42.245.642/0001-09",
                "country_id": self.env.ref("base.br").id,
                "state_id": self.env.ref("base.state_br_sp").id,
            }
        )
        return company

    def _switch_user_company(self, user, company):
        """ Add a company to the user's allowed & set to current. """
        user.write(
            {
                "company_ids": [(6, 0, (company + user.company_ids).ids)],
                "company_id": company.id,
            }
        )

    def test_valid_certificate(self):
        """Create and check a valid certificate"""
        cert = self.certificate_model.create(
            {
                "type": "nf-e",
                "subtype": "a1",
                "password": self.cert_passwd,
                "file": self.certificate_valid,
            }
        )

        self.assertEqual(cert.issuer_name, self.cert_issuer_a)
        self.assertEqual(cert.owner_name, self.cert_subject_valid)
        self.assertEqual(cert.date_expiration.year, self.cert_date_exp.year)
        self.assertEqual(cert.date_expiration.month, self.cert_date_exp.month)
        self.assertEqual(cert.date_expiration.day, self.cert_date_exp.day)
        self.assertEqual(cert.name, self.cert_name)
        self.assertEqual(cert.is_valid, True)

    def test_certificate_wrong_password(self):
        """Write a valid certificate with wrong password"""
        with self.assertRaises(ValidationError):
            self.certificate_model.create(
                {
                    "type": "nf-e",
                    "subtype": "a1",
                    "password": "INVALID",
                    "file": self.certificate_valid,
                }
            )

    def test_invalid_certificate(self):
        """Create and check a invalid certificate"""
        with self.assertRaises(ValidationError):
            self.certificate_model.create(
                {
                    "type": "nf-e",
                    "subtype": "a1",
                    "password": self.cert_passwd,
                    "file": self.certificate_invalid,
                }
            )
