# @ 2017 Akretion - www.akretion.com.br -
#   Clément Mombereau <clement.mombereau@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests.common import TransactionCase


class L10nBrCrmOnchangeTest(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.crm_lead_01 = cls.env["crm.lead"].create(
            {
                "name": "Test Company Lead",
                "partner_name": "Test Company",
                "legal_name": "Test Company LTDA",
                "contact_name": "Test Name Contact",
                "name_surname": "Test NameSurname Contact",
                "cnpj": "56.647.352/0001-98",
                "city_id": cls.env.ref("l10n_br_base.city_3205002").id,
                "country_id": cls.env.ref("base.br").id,
                "zip": "29161-695",
                "cpf": "70531160505",
                "email_from": "testcontact@email.com",
                "phone": "999999999",
            }
        )

    def test_onchange(self):
        """
        Call all the onchange methods in l10n_br_crm
        """
        self.crm_lead_01._onchange_cnpj()
        self.crm_lead_01._onchange_mask_cpf()
        self.crm_lead_01._onchange_city_id()
        self.crm_lead_01._onchange_zip()
        self.crm_lead_01.partner_id = self.crm_lead_01._create_customer()
        self.crm_lead_01._onchange_partner_id()
