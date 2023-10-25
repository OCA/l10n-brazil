# Copyright 2023 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests import SavepointCase


class TestL10nBrPosPartner(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.pos_config = cls.env.ref("point_of_sale.pos_config_main")

    def test_create_partner_from_ui_l10n_brazil(self):
        partner_vals = {
            "country_id": 31,
            "state_id": 95,
            "property_product_pricelist": 1,
            "name": "Consumidor PDV",
            "street": "Parque dos Bancários",
            "city": "São Paulo",
            "zip": "03923-095",
            "email": "consumidor.pdv@email.com.br",
            "phone": "111111111",
            "id": False,
            "vat": "392.812.628-86",
        }

        self.env["res.partner"].create_from_ui(partner_vals)

        partner = self.env["res.partner"].search([("name", "=", "Consumidor PDV")])
        self.assertEqual(1, len(partner), "Error creating the partner from UI.")

    def test_create_company_partner_from_ui_l10n_brazil(self):
        company_partner_vals = {
            "country_id": 31,
            "state_id": 95,
            "property_product_pricelist": 1,
            "name": "Empresa PDV",
            "street": "Parque dos Bancários",
            "city": "São Paulo",
            "zip": "03923-095",
            "email": "empresa.pdv@email.com.br",
            "phone": "11111111",
            "id": False,
            "vat": "06.870.693/0001-50",
        }
        self.env["res.partner"].create_from_ui(company_partner_vals)

        partner = self.env["res.partner"].search([("name", "=", "Empresa PDV")])
        self.assertEqual(1, len(partner), "Error creating the company_partner from UI.")
