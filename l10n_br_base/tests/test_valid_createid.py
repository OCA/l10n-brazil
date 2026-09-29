# @ 2017 Akretion - www.akretion.com.br -
#   Clément Mombereau <clement.mombereau@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase


class ValidCreateIdTest(TransactionCase):
    """Test if ValidationError is raised well during create({})"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.company_valid = {
            "name": "Company Test 1",
            "legal_name": "Company Testc 1 Ltda",
            "vat": "02.960.895/0001-31",
            "l10n_br_ie_code": "081.981.37-6",
            "street": "Rod BR-101 Norte Contorno",
            "street_number": "955",
            "street2": "Portão 1",
            "district": "Jardim da Saudade",
            "state_id": cls.env.ref("base.state_br_es").id,
            "city_id": cls.env.ref("l10n_br_base.city_3205002").id,
            "country_id": cls.env.ref("base.br").id,
            "city": "Serra",
            "zip": "29161-695",
            "phone": "+55 27 2916-1695",
            "email": "contact@companytest.com.br",
            "website": "www.companytest.com.br",
        }

        cls.company_invalid_cnpj = {
            "name": "Company Test 2",
            "legal_name": "Company Testc 2 Ltda",
            "vat": "14.018.406/0001-93",
            "l10n_br_ie_code": "385.611.86-2",
            "street": "Rod BR-101 Norte Contorno",
            "street_number": "955",
            "street2": "Portão 1",
            "district": "Jardim da Saudade",
            "state_id": cls.env.ref("base.state_br_es").id,
            "city_id": cls.env.ref("l10n_br_base.city_3205002").id,
            "country_id": cls.env.ref("base.br").id,
            "city": "Serra",
            "zip": "29161-695",
            "phone": "+55 27 2916-1695",
            "email": "contact@companytest.com.br",
            "website": "www.companytest.com.br",
        }

        cls.company_invalid_l10n_br_ie_code = {
            "name": "Company Test 3",
            "legal_name": "Company Testc 3 Ltda",
            "vat": "31.295.101/0001-60",
            "l10n_br_ie_code": "924.511.27-0",
            "street": "Rod BR-101 Norte Contorno",
            "street_number": "955",
            "street2": "Portão 1",
            "district": "Jardim da Saudade",
            "state_id": cls.env.ref("base.state_br_es").id,
            "city_id": cls.env.ref("l10n_br_base.city_3205002").id,
            "country_id": cls.env.ref("base.br").id,
            "city": "Serra",
            "zip": "29161-695",
            "phone": "+55 27 2916-1695",
            "email": "contact@companytest.com.br",
            "website": "www.companytest.com.br",
        }

        cls.partner_valid = {
            "name": "Partner Test 1",
            "legal_name": "Partner Testc 1 Ltda",
            "vat": "734.419.622-06",
            "l10n_br_ie_code": "176.754.07-5",
            "street": "Rod BR-101 Norte Contorno",
            "street_number": "955",
            "street2": "Portão 1",
            "district": "Jardim da Saudade",
            "state_id": cls.env.ref("base.state_br_es").id,
            "city_id": cls.env.ref("l10n_br_base.city_3205002").id,
            "country_id": cls.env.ref("base.br").id,
            "city": "Serra",
            "zip": "29161-695",
            "phone": "+55 27 2916-1695",
            "email": "contact@partnertest.com.br",
            "website": "www.partnertest.com.br",
        }

        cls.partner_invalid_cpf = {
            "name": "Partner Test 2",
            "legal_name": "Partner Testc 2 Ltda",
            "vat": "734.419.622-07",
            "l10n_br_ie_code": "538.759.92-5",
            "street": "Rod BR-101 Norte Contorno",
            "street_number": "955",
            "street2": "Portão 1",
            "district": "Jardim da Saudade",
            "state_id": cls.env.ref("base.state_br_es").id,
            "city_id": cls.env.ref("l10n_br_base.city_3205002").id,
            "country_id": cls.env.ref("base.br").id,
            "city": "Serra",
            "zip": "29161-695",
            "phone": "+55 27 2916-1695",
            "email": "contact@partnertest.com.br",
            "website": "www.partnertest.com.br",
        }

        cls.partner_outside_br = {
            "name": "Partner Test 3",
            "legal_name": "Partner Tesc 3 Ltda",
            "vat": "123456789",
            "street": "Street Company",
            "street_number": "955",
            "street2": "Street2 Company",
            "district": "Company District",
            "state_id": cls.env.ref("base.state_us_2").id,
            "country_id": cls.env.ref("base.us").id,
            "city": "Nome",
            "zip": "99762",
            "phone": "+1 (907) 443-5796",
            "email": "contact@companytest.com.br",
            "website": "www.companytest.com.br",
        }

    # Tests on companies

    def test_comp_valid(self):
        """Try do create id with correct CNPJ and correct Inscricao Estadual"""
        company = (
            self.env["res.company"]
            .with_context(tracking_disable=True)
            .create(self.company_valid)
        )
        self.assertTrue(company.id, "Error when using .create() with a valid CNPJ")

    def test_comp_invalid_cnpj(self):
        """Test if ValidationError raised during .create() with invalid CNPJ
        and correct Inscricao Estadual"""
        with self.assertRaises(ValidationError):
            self.env["res.company"].with_context(tracking_disable=True).create(
                self.company_invalid_cnpj
            )

    def test_comp_invalid_l10n_br_ie_code(self):
        """Test if ValidationError raised with correct CNPJ
        and invalid Inscricao Estadual"""
        with self.assertRaises(ValidationError):
            self.env["res.company"].with_context(tracking_disable=True).create(
                self.company_invalid_l10n_br_ie_code
            )

    # Tests on partners

    def test_part_valid(self):
        """Try do create id with correct CPF and correct Inscricao Estadual"""
        partner = (
            self.env["res.partner"]
            .with_context(tracking_disable=True)
            .create(self.partner_valid)
        )
        self.assertTrue(partner.id, "Error when using .create() with a valid CPF")

    def test_part_invalid_cpf(self):
        """Test if ValidationError raised during .create() with invalid CPF
        and correct Inscricao Estadual"""
        with self.assertRaises(ValidationError):
            self.env["res.partner"].with_context(tracking_disable=True).create(
                self.partner_invalid_cpf
            )

    def test_vat_computation_with_cpf(self):
        """Test vat computation for a br partner with CPF"""
        partner = (
            self.env["res.partner"]
            .with_context(tracking_disable=True)
            .create(self.partner_valid)
        )
        self.assertEqual(
            partner.vat,
            "73441962206",
            "vat should be unformatted CPF for a br partner",
        )
        self.assertEqual(
            partner.vat_formatted_cnpj,
            "734.419.622-06",
            "vat_formatted_cnpj should be formatted CPF",
        )

    def test_vat_computation_without_cnpj(self):
        """Test VAT computation for a br partner without CNPJ"""
        partner_data = self.partner_valid.copy()
        partner_data.pop("vat")
        partner = (
            self.env["res.partner"]
            .with_context(tracking_disable=True)
            .create(partner_data)
        )
        self.assertFalse(
            partner.vat, "VAT should be False for a br partner without CNPJ"
        )

    def test_vat_computation_outside_company_with_vat(self):
        """Test VAT computation for a outside br partner with VAT"""
        partner = (
            self.env["res.partner"]
            .with_context(tracking_disable=True)
            .create(self.partner_outside_br)
        )
        self.assertEqual(
            partner.vat,
            "123456789",
            "The VAT must be the same as what was registered",
        )

    def test_vat_computation_outside_company_without_vat(self):
        """Test VAT computation for a outside br partner without VAT"""
        partner_data = self.partner_outside_br.copy()
        partner_data.pop("vat")
        partner = (
            self.env["res.partner"]
            .with_context(tracking_disable=True)
            .create(partner_data)
        )
        self.assertFalse(partner.vat, "VAT should be False as registered")

    def test_vat_computation_with_cnpj_and_vat(self):
        """Test VAT computation for a br partner with a CNPJ"""
        partner_data = self.partner_valid.copy()
        partner_data.pop("vat")
        partner_data.update(
            {
                "vat": "93.429.799/0001-17",
            }
        )
        partner = (
            self.env["res.partner"]
            .with_context(tracking_disable=True)
            .create(partner_data)
        )
        self.assertEqual(  # FIXME
            partner.vat,
            "93429799000117",
            "The VAT must be unformatted as stored by core Odoo",
        )
        self.assertEqual(
            partner.vat_formatted_cnpj,
            "93.429.799/0001-17",
            "The VAT/CNPJ must be formatted for display",
        )

    def test_is_company_with_cnpj(self):
        """A partner holding a CNPJ is a company"""
        partner_data = self.partner_valid.copy()
        partner_data.update(
            {
                "vat": "93.429.799/0001-17",
            }
        )
        partner = (
            self.env["res.partner"]
            .with_context(tracking_disable=True)
            .create(partner_data)
        )
        self.assertTrue(
            partner.is_company,
            "A partner with a CNPJ must be considered a company",
        )

    def test_is_company_with_cpf(self):
        """A partner holding a CPF is an individual"""
        partner = (
            self.env["res.partner"]
            .with_context(tracking_disable=True)
            .create(self.partner_valid)
        )
        self.assertFalse(
            partner.is_company,
            "A partner with a CPF must not be considered a company",
        )

    def test_is_company_outside_brazil(self):
        """A foreign partner keeps the core behaviour (a VAT means a company)"""
        partner = (
            self.env["res.partner"]
            .with_context(tracking_disable=True)
            .create(self.partner_outside_br)
        )
        self.assertTrue(
            partner.is_company,
            "A foreign partner with a VAT must keep the core behaviour",
        )


# No test on Inscricao Estadual for partners with CPF
# because they haven't Inscricao Estadual
