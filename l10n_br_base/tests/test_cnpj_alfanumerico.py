# Copyright (C) 2026-Today - Escodoo (<https://www.escodoo.com.br>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase

from .tools import load_fixture_files


class CNPJAlfanumericoTest(TransactionCase):
    """Tests for alphanumeric CNPJ support (CNPJ Alfanumérico - Receita Federal)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        load_fixture_files(
            cls.env,
            "l10n_br_base",
            file_names=["l10n_br_base_demo.xml"],
        )

        cls.br_country = cls.env.ref("base.br")
        cls.state_es = cls.env.ref("base.state_br_es")
        cls.city_serra = cls.env.ref("l10n_br_base.city_3205002")

        cls.base_address = {
            "street": "Av. Paulista",
            "street_number": "1000",
            "district": "Bela Vista",
            "state_id": cls.state_es.id,
            "city_id": cls.city_serra.id,
            "country_id": cls.br_country.id,
            "city": "Serra",
            "zip": "29161-695",
        }

        cls.partner_pix = cls.env.ref("l10n_br_base.res_partner_amd")

    def test_company_valid_alphanumeric_cnpj(self):
        """Creating a company with a valid alphanumeric CNPJ must succeed."""
        vals = {
            "name": "Empresa CNPJ Alfa Teste",
            "legal_name": "Empresa CNPJ Alfanumérico Ltda",
            "vat": "A8.7HB.ZHB/0001-61",
            **self.base_address,
        }
        company = (
            self.env["res.company"].with_context(tracking_disable=True).create(vals)
        )
        self.assertTrue(company.id, "Company with alphanumeric CNPJ was not created")
        self.assertEqual(
            company.vat,
            "A87HBZHB000161",
            "Unformatted alphanumeric CNPJ should be preserved",
        )
        self.assertEqual(
            company.vat_formatted_cnpj,
            "A8.7HB.ZHB/0001-61",
            "Formatted alphanumeric CNPJ should be available",
        )
        self.assertEqual(
            company.cnpj_cpf_stripped,
            "A87HBZHB000161",
            "Stripped alphanumeric CNPJ should contain only alphanumeric characters",
        )

    def test_company_invalid_alphanumeric_cnpj(self):
        """Creating a company with an invalid alphanumeric CNPJ must raise
        ValidationError."""
        vals = {
            "name": "Empresa CNPJ Alfa Invalido",
            "legal_name": "Empresa CNPJ Alfanumérico Inválido Ltda",
            "vat": "A8.7HB.ZHB/0001-99",
            **self.base_address,
        }
        with self.assertRaises(ValidationError):
            self.env["res.company"].with_context(tracking_disable=True).create(vals)

    def test_partner_valid_alphanumeric_cnpj(self):
        """Creating a partner (company type) with a valid alphanumeric CNPJ
        must succeed."""
        vals = {
            "name": "Parceiro CNPJ Alfa Teste",
            "legal_name": "Parceiro CNPJ Alfanumérico Ltda",
            "is_company": True,
            "vat": "A8.7HB.ZHB/0001-61",
            **self.base_address,
        }
        partner = (
            self.env["res.partner"].with_context(tracking_disable=True).create(vals)
        )
        self.assertTrue(partner.id, "Partner with alphanumeric CNPJ was not created")
        self.assertTrue(
            partner.is_br_partner,
            "Partner with alphanumeric CNPJ should be recognized as Brazilian",
        )

    def test_partner_alphanumeric_cnpj_stripped(self):
        """cnpj_cpf_stripped must contain only alphanumeric characters (no mask)."""
        vals = {
            "name": "Parceiro Stripped Alfa",
            "is_company": True,
            "vat": "A8.7HB.ZHB/0001-61",
            **self.base_address,
        }
        partner = (
            self.env["res.partner"].with_context(tracking_disable=True).create(vals)
        )
        self.assertEqual(partner.cnpj_cpf_stripped, "A87HBZHB000161")

    def test_partner_write_alphanumeric_cnpj(self):
        """Writing an alphanumeric CNPJ on an existing partner must succeed.

        Only the create path was covered before, so a formatting helper
        that dropped the letters and validated the remaining digits as a
        CPF went unnoticed on write.
        """
        partner = (
            self.env["res.partner"]
            .with_context(tracking_disable=True)
            .create(
                {
                    "name": "Parceiro Write Alfa",
                    "is_company": True,
                    "vat": "77.889.900/0001-66",
                    **self.base_address,
                }
            )
        )

        partner.write({"vat": "99.XYZ.888/0001-50"})

        self.assertEqual(partner.cnpj_cpf_stripped, "99XYZ888000150")
        self.assertEqual(partner.vat_formatted_cnpj, "99.XYZ.888/0001-50")

    def test_partner_write_numeric_over_alphanumeric_cnpj(self):
        """Replacing an alphanumeric CNPJ with a numeric one must keep
        working, so the fix does not regress the plain numeric path."""
        partner = (
            self.env["res.partner"]
            .with_context(tracking_disable=True)
            .create(
                {
                    "name": "Parceiro Write Numerico",
                    "is_company": True,
                    "vat": "12.ABC.345/01DE-35",
                    **self.base_address,
                }
            )
        )

        partner.write({"vat": "44.556.677/0001-86"})

        self.assertEqual(partner.cnpj_cpf_stripped, "44556677000186")
        self.assertEqual(partner.vat_formatted_cnpj, "44.556.677/0001-86")

    def test_company_write_alphanumeric_cnpj(self):
        """Writing an alphanumeric CNPJ on an existing company must succeed."""
        company = (
            self.env["res.company"]
            .with_context(tracking_disable=True)
            .create(
                {
                    "name": "Empresa Write Alfa",
                    "legal_name": "Empresa Write Alfa Ltda",
                    "vat": "11.222.333/0001-81",
                    **self.base_address,
                }
            )
        )

        company.write({"vat": "11.AAA.222/0001-64"})

        self.assertEqual(company.vat, "11AAA222000164")
        self.assertEqual(company.cnpj_cpf_stripped, "11AAA222000164")

    def test_pix_valid_alphanumeric_cnpj(self):
        """Creating a PIX key with a valid alphanumeric CNPJ must succeed."""
        pix_vals = {
            "partner_id": self.partner_pix.id,
            "key_type": "cnpj_cpf",
            "key": "LC.X4R.RVT/0001-23",
        }
        pix = (
            self.env["res.partner.pix"]
            .with_context(tracking_disable=True)
            .create(pix_vals)
        )
        self.assertTrue(pix.id, "PIX key with alphanumeric CNPJ was not created")

    def test_pix_invalid_alphanumeric_cnpj(self):
        """Creating a PIX key with an invalid alphanumeric CNPJ must raise
        ValidationError."""
        pix_vals = {
            "partner_id": self.partner_pix.id,
            "key_type": "cnpj_cpf",
            "key": "LC.X4R.RVT/0001-99",
        }
        with self.assertRaises(ValidationError):
            self.env["res.partner.pix"].with_context(tracking_disable=True).create(
                pix_vals
            )

    def test_pix_alphanumeric_cnpj_without_mask(self):
        """PIX key with unmasked valid alphanumeric CNPJ must succeed."""
        pix_vals = {
            "partner_id": self.partner_pix.id,
            "key_type": "cnpj_cpf",
            "key": "LCX4RRVT000123",
        }
        pix = (
            self.env["res.partner.pix"]
            .with_context(tracking_disable=True)
            .create(pix_vals)
        )
        self.assertTrue(
            pix.id, "PIX key with unmasked alphanumeric CNPJ was not created"
        )
