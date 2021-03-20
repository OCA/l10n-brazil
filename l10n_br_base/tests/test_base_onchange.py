# @ 2017 Akretion - www.akretion.com.br -
#   Clément Mombereau <clement.mombereau@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests import SavepointCase


class L10nBrBaseOnchangeTest(SavepointCase):

    @classmethod
    def setUpClass(self):
        super().setUpClass()

        self.company_01 = self.env["res.company"].with_context(
            tracking_disable=True).create(
                {
                    "name": "Company Test 1",
                    "cnpj_cpf": "02.960.895/0001-31",
                    "city_id": self.env.ref("l10n_br_base.city_3205002").id,
                    "zip": "29161-695",
                }
            )

        self.bank_01 = self.env["res.bank"].create(
            {"name": "Bank Test 1", "zip": "29161-695"}
        )

        self.partner_01 = self.env["res.partner"].with_context(
            tracking_disable=True).create(
                {"name": "Partner Test 01", "zip": "29161-695"}
            )

    def test_onchange(self):
        """
        Call all the onchange methods in l10n_br_base
        """
        self.company_01._onchange_cnpj_cpf()
        self.company_01._onchange_city_id()
        self.company_01._onchange_zip()
        self.company_01._onchange_state()

        self.partner_01._onchange_cnpj_cpf()
        self.partner_01._onchange_city_id()
        self.partner_01._onchange_zip()

    def test_inverse_fields(self):
        self.company_01.inscr_mun = "692015742119"
        self.assertEquals(
            self.company_01.partner_id.inscr_mun,
            "692015742119",
            "The inverse function to field inscr_mun failed.",
        )
        self.company_01.suframa = "1234"
        self.assertEquals(
            self.company_01.partner_id.suframa,
            "1234",
            "The inverse function to field suframa failed.",
        )

    def test_display_address(self):
        partner = self.env.ref("l10n_br_base.res_partner_akretion")
        partner._onchange_city_id()
        display_address = partner._display_address()
        self.assertEquals(
            display_address,
            "Akretion Sao Paulo\n"
            "Avenida Paulista, 807 CJ 2315\nCentro"
            "\n01311-915 - São Paulo-SP\nBrazil",
            "The function _display_address failed.",
        )

    def test_display_address_parent_id(self):
        partner = self.env.ref("l10n_br_base.res_partner_address_ak2")
        partner._onchange_city_id()
        display_address = partner._display_address()
        self.assertEquals(
            display_address,
            "Akretion Rio de Janeiro\n"
            "Rua Acre, 47 sala 1310\nCentro"
            "\n20081-000 - Rio de Janeiro-RJ\nBrazil",
            "The function _display_address with parent_id failed.",
        )

    def test_other_country_display_address(self):
        partner = self.env.ref("l10n_br_base.res_partner_exterior")
        display_address = partner._display_address()
        self.assertEquals(
            display_address,
            "Cliente Exterior\n3404  Edgewood"
            " Road\n\nJonesboro"
            " AR 72401\nUnited States",
            "The function _display_address for other country failed.",
        )

    def test_display_address_without_company(self):
        partner = self.env.ref("l10n_br_base.res_partner_akretion")
        partner._onchange_city_id()
        display_address = partner._display_address(without_company=True)
        self.assertEquals(
            display_address,
            "Avenida Paulista, 807 CJ 2315\nCentro"
            "\n01311-915 - São Paulo-SP\nBrazil",
            "The function _display_address with parameter"
            " without_company failed.",
        )
