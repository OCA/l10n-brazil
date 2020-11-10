# @ 2017 Akretion - www.akretion.com.br -
#   Clément Mombereau <clement.mombereau@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.exceptions import ValidationError
from odoo.tests import SavepointCase


class ValidCreateIdTest(SavepointCase):
    """Test if ValidationError is raised well during create({})"""

    @classmethod
    def setUpClass(self):
        super().setUpClass()

        self.company_valid = {
            "name": "Company Test 1",
            "legal_name": "Company Testc 1 Ltda",
            "cnpj_cpf": "02.960.895/0001-31",
            "inscr_est": "081.981.37-6",
            "street": "Rod BR-101 Norte Contorno",
            "street_number": "955",
            "street2": "Portão 1",
            "district": "Jardim da Saudade",
            "state_id": self.env.ref("base.state_br_es").id,
            "city_id": self.env.ref("l10n_br_base.city_3205002").id,
            "country_id": self.env.ref("base.br").id,
            "city": "Serra",
            "zip": "29161-695",
            "phone": "+55 27 2916-1695",
            "email": "contact@companytest.com.br",
            "website": "www.companytest.com.br",
        }

        self.company_invalid_cnpj = {
            "name": "Company Test 2",
            "legal_name": "Company Testc 2 Ltda",
            "cnpj_cpf": "14.018.406/0001-93",
            "inscr_est": "385.611.86-2",
            "street": "Rod BR-101 Norte Contorno",
            "street_number": "955",
            "street2": "Portão 1",
            "district": "Jardim da Saudade",
            "state_id": self.env.ref("base.state_br_es").id,
            "city_id": self.env.ref("l10n_br_base.city_3205002").id,
            "country_id": self.env.ref("base.br").id,
            "city": "Serra",
            "zip": "29161-695",
            "phone": "+55 27 2916-1695",
            "email": "contact@companytest.com.br",
            "website": "www.companytest.com.br",
        }

        self.company_invalid_inscr_est = {
            "name": "Company Test 3",
            "legal_name": "Company Testc 3 Ltda",
            "cnpj_cpf": "31.295.101/0001-60",
            "inscr_est": "924.511.27-0",
            "street": "Rod BR-101 Norte Contorno",
            "street_number": "955",
            "street2": "Portão 1",
            "district": "Jardim da Saudade",
            "state_id": self.env.ref("base.state_br_es").id,
            "city_id": self.env.ref("l10n_br_base.city_3205002").id,
            "country_id": self.env.ref("base.br").id,
            "city": "Serra",
            "zip": "29161-695",
            "phone": "+55 27 2916-1695",
            "email": "contact@companytest.com.br",
            "website": "www.companytest.com.br",
        }

        self.partner_valid = {
            "name": "Partner Test 1",
            "legal_name": "Partner Testc 1 Ltda",
            "cnpj_cpf": "734.419.622-06",
            "inscr_est": "176.754.07-5",
            "street": "Rod BR-101 Norte Contorno",
            "street_number": "955",
            "street2": "Portão 1",
            "district": "Jardim da Saudade",
            "state_id": self.env.ref("base.state_br_es").id,
            "city_id": self.env.ref("l10n_br_base.city_3205002").id,
            "country_id": self.env.ref("base.br").id,
            "city": "Serra",
            "zip": "29161-695",
            "phone": "+55 27 2916-1695",
            "email": "contact@partnertest.com.br",
            "website": "www.partnertest.com.br",
        }

        self.partner_invalid_cpf = {
            "name": "Partner Test 2",
            "legal_name": "Partner Testc 2 Ltda",
            "cnpj_cpf": "734.419.622-07",
            "inscr_est": "538.759.92-5",
            "street": "Rod BR-101 Norte Contorno",
            "street_number": "955",
            "street2": "Portão 1",
            "district": "Jardim da Saudade",
            "state_id": self.env.ref("base.state_br_es").id,
            "city_id": self.env.ref("l10n_br_base.city_3205002").id,
            "country_id": self.env.ref("base.br").id,
            "city": "Serra",
            "zip": "29161-695",
            "phone": "+55 27 2916-1695",
            "email": "contact@partnertest.com.br",
            "website": "www.partnertest.com.br",
        }

    # Tests on companies

    def test_comp_valid(self):
        """Try do create id with correct CNPJ and correct Inscricao Estadual"""
        try:
            company = self.env["res.company"].with_context(
                tracking_disable=True).create(self.company_valid)
        except:
            assert (
                company
            ), "Error when using .create() even with valid \
                             and Inscricao Estadual"

    def test_comp_invalid_cnpj(self):
        """Test if ValidationError raised during .create() with invalid CNPJ
            and correct Inscricao Estadual"""
        with self.assertRaises(ValidationError):
            self.env["res.company"].with_context(
                tracking_disable=True).create(self.company_invalid_cnpj)

    def test_comp_invalid_inscr_est(self):
        """Test if ValidationError raised with correct CNPJ
            and invalid Inscricao Estadual"""
        with self.assertRaises(ValidationError):
            self.env["res.company"].with_context(
                tracking_disable=True).create(self.company_invalid_inscr_est)

    # Tests on partners

    def test_part_valid(self):
        """Try do create id with correct CPF and correct Inscricao Estadual"""
        try:
            partner = self.env["res.partner"].with_context(
                tracking_disable=True).create(self.partner_valid)
        except:
            assert (
                partner
            ), "Error when using .create() even with valid CPF \
                         and Inscricao Estadual"

    def test_part_invalid_cpf(self):
        """Test if ValidationError raised during .create() with invalid CPF
            and correct Inscricao Estadual"""
        with self.assertRaises(ValidationError):
            self.env["res.partner"].with_context(
                tracking_disable=True).create(self.partner_invalid_cpf)


# No test on Inscricao Estadual for partners with CPF
# because they haven't Inscricao Estadual
