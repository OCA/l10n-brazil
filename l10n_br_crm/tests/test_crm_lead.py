# @ 2017 Akretion - www.akretion.com.br -
#   Clément Mombereau <clement.mombereau@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests.common import TransactionCase


class CrmLeadTest(TransactionCase):
    """Test basic operations on Lead"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Create lead with simple details
        cls.crm_lead_company = cls.env["crm.lead"].create(
            {
                "name": "Test Company Lead",
                "legal_name": "Teste Empresa",
                "cnpj": "56.647.352/0001-98",
                "stage_id": cls.env.ref("crm.stage_lead1").id,
                "partner_name": "Test Partner",
                "l10n_br_ie_code": "079.798.013.363",
                "l10n_br_im_code": "99999999",
            }
        )

        # Create lead for a person/contact
        cls.crm_lead_contact = cls.env["crm.lead"].create(
            {
                "name": "Test Contact",
                "cpf": "70531160505",
                "l10n_br_rg_code": "99.888.777-1",
                "stage_id": cls.env.ref("crm.stage_lead1").id,
                "contact_name": "Test Contact",
            }
        )

        # Create lead with a valid Inscr. Estadual
        cls.crm_lead_company_1 = cls.env["crm.lead"].create(
            {
                "name": "Test Company Lead IE",
                "legal_name": "Teste Empresa 1",
                "cnpj": "57.240.310/0001-09",
                "stage_id": cls.env.ref("crm.stage_lead1").id,
                "partner_name": "Test Partner 1",
                "l10n_br_ie_code": "041.092.540.590",
                "l10n_br_im_code": "99999999",
                "country_id": cls.env.ref("base.br").id,
                "state_id": cls.env.ref("base.state_br_sp").id,
            }
        )

        # Create a Partner
        cls.partner_id_01 = cls.env["res.partner"].create(
            {
                "name": "Test Lead Partner",
                "legal_name": "Test Lead Partner",
                "cnpj_cpf": "22.898.817/0001-61",
                "l10n_br_ie_code": "041.092.540.590",
                "l10n_br_im_code": "99999999",
                "l10n_br_isuf_code": "99999999",
                "street_number": "1225",
                "district": "centro",
                "city_id": cls.env.ref("l10n_br_base.city_4205407").id,
                "is_company": True,
            }
        )

    # Tests on crm_lead_company :

    def test_conversion(self):
        """Test to convert a Lead into an opportunity"""

        # Mark the lead as lost in order to test the conversion
        self.crm_lead_company.action_set_lost()

        # Set lead to Open stage
        self.crm_lead_company.write(
            {"stage_id": self.env.ref("crm.stage_lead1").id, "active": True}
        )
        # Check if the lead stage is "Open".
        self.assertEqual(
            self.crm_lead_company.stage_id.sequence, 1, "Lead stage is not Open"
        )
        # Convert lead into opportunity for exiting customer
        self.crm_lead_company.convert_opportunity(self.env.ref("base.res_partner_2"))

        # Check details of converted opportunity
        self.assertEqual(
            self.crm_lead_company.type,
            "opportunity",
            "Lead is not converted to opportunity!",
        )
        self.assertEqual(
            self.crm_lead_company.partner_id.id,
            self.env.ref("base.res_partner_2").id,
            "Partner mismatch!",
        )
        self.assertEqual(
            self.crm_lead_company.stage_id.id,
            self.env.ref("crm.stage_lead1").id,
            "Stage of opportunity is incorrect!",
        )

    def test_create_partner(self):
        """Create a Partner and check the if the fields were filled"""
        self.partner_id = self.crm_lead_company._create_customer()

        self.obj_partner = self.env["res.partner"].browse(self.partner_id.id)

        self.assertTrue(
            self.obj_partner.name, "The creation of the partner have problems."
        )
        self.assertTrue(
            self.obj_partner.legal_name, "The field Razão Social not was filled."
        )
        self.assertTrue(self.obj_partner.cnpj_cpf, "The field CNPJ not was filled.")
        self.assertTrue(
            self.obj_partner.l10n_br_ie_code,
            "The field Inscrição Estadual not was filled",
        )
        self.assertTrue(
            self.obj_partner.l10n_br_im_code,
            "The field Inscrição Municipal not was filled",
        )

    def test_lead_won(self):
        """Test to mark the Lead as won"""
        self.crm_lead_company.action_set_won()

    # Tests on crm_lead_contact

    def test_conversion_contact(self):
        """Test to convert a Lead"""

        # Mark the lead as lost
        self.crm_lead_contact.action_set_lost()

        # Set lead to Open stage
        self.crm_lead_contact.write(
            {"stage_id": self.env.ref("crm.stage_lead1").id, "active": True}
        )
        # Check if the lead stage is "Open".
        self.assertEqual(
            self.crm_lead_contact.stage_id.sequence, 1, "Lead stage is not Open"
        )
        # Convert lead into opportunity for exiting customer
        self.crm_lead_contact.convert_opportunity(self.env.ref("base.res_partner_2"))

        # Check details of converted opportunity
        self.assertEqual(
            self.crm_lead_contact.type,
            "opportunity",
            "Lead is not converted to opportunity!",
        )
        self.assertEqual(
            self.crm_lead_contact.partner_id.id,
            self.env.ref("base.res_partner_2").id,
            "Partner mismatch!",
        )
        self.assertEqual(
            self.crm_lead_contact.stage_id.id,
            self.env.ref("crm.stage_lead1").id,
            "Stage of opportunity is incorrect!",
        )

    def test_create_contact(self):
        """Create a Contact and check the if the fields were filled"""
        self.partner_id = self.crm_lead_contact._create_customer()
        self.obj_partner = self.env["res.partner"].browse(self.partner_id.id)

        self.assertTrue(self.obj_partner.name, "The field Name was not filled.")
        self.assertTrue(self.obj_partner.cnpj_cpf, "The field CNPJ was not filled.")
        self.assertTrue(self.obj_partner.l10n_br_ie_code, "The field RG was not filled")

    def test_lead_won_contact(self):
        """Test to mark the Lead as won"""
        self.crm_lead_company.action_set_won()

    # Tests on crm_lead_company_1

    def test_create_partner_IE(self):
        """
        Create a partner of crm_lead_company_1 and
        check if the fields were fields with Inscr. Estadual ok
        """
        self.partner_id = self.crm_lead_company_1._create_customer()

        self.obj_partner = self.env["res.partner"].browse(self.partner_id.id)

        self.assertTrue(
            self.obj_partner.name, "The creation of the partner have problems."
        )
        self.assertTrue(
            self.obj_partner.legal_name, "The field Razão Social not was filled."
        )
        self.assertTrue(self.obj_partner.cnpj_cpf, "The field CNPJ not was filled.")
        self.assertTrue(
            self.obj_partner.l10n_br_ie_code,
            "The field Inscrição Estadual not was filled",
        )
        self.assertTrue(
            self.obj_partner.l10n_br_im_code,
            "The field Inscrição Municipal not was filled",
        )
        self.assertTrue(self.obj_partner.country_id, "The field Country not was filled")
        self.assertTrue(self.obj_partner.state_id, "The field State not was filled")

    def test_change_lead_partner(self):
        """
        Test if the partner's lead infos change
        after changing the partner
        """
        self.crm_lead_company_1.partner_id = self.partner_id_01
        self.crm_lead_company_1._onchange_partner_id()

        self.assertEqual(
            self.crm_lead_company_1.legal_name,
            "Test Lead Partner",
            "In the change of the partner \
                         the field legal_name was not automatically filled.",
        )

        self.assertEqual(
            self.crm_lead_company_1.cnpj,
            "22.898.817/0001-61",
            "In the change of the partner \
                         the field cpf was not automatically filled.",
        )

        self.assertEqual(
            self.crm_lead_company_1.l10n_br_ie_code,
            "041.092.540.590",
            "In the change of the partner \
                         the field l10n_br_ie_code was not automatically filled.",
        )

        self.assertEqual(
            self.crm_lead_company_1.l10n_br_im_code,
            "99999999",
            "In the change of the partner \
                         the field l10n_br_im_code was not automatically filled.",
        )

        self.assertEqual(
            self.crm_lead_company_1.l10n_br_isuf_code,
            "99999999",
            "In the change of the partner \
                         the field l10n_br_isuf_code was not automatically filled.",
        )

        self.assertEqual(
            self.crm_lead_company_1.street_number,
            "1225",
            "In the change of the partner \
                         the field number was not automatically filled.",
        )

        self.assertEqual(
            self.crm_lead_company_1.district,
            "centro",
            "In the change of the partner \
                         the field district was not automatically filled.",
        )

        self.assertEqual(
            self.crm_lead_company_1.city_id.id,
            self.env.ref("l10n_br_base.city_4205407").id,
            "In the change of the partner the field \
                         city_id was not automatically filled.",
        )

    def test_brazilian_fields_in_lead_view(self):
        """
        Test when show Brazilian Fields in the Lead View.
        """
        # Brazilian Lead with Partner informed
        self.assertTrue(
            self.crm_lead_company_1.show_l10n_br,
            "Field show_l10n_br should be True for Brazilian case.",
        )

        # Brazilian Lead without Partner
        lead_without_partner = self.env["crm.lead"].create(
            {
                "name": "Test BR without Partner",
                "stage_id": self.env.ref("crm.stage_lead1").id,
                "country_id": self.env.ref("base.br").id,
            }
        )
        self.assertTrue(
            lead_without_partner.show_l10n_br,
            "Field show_l10n_br should be True for Brazilian case.",
        )

        # International Lead
        inter_lead = self.env.ref("crm.crm_case_31")
        self.assertFalse(
            inter_lead.show_l10n_br,
            "Field show_l10n_br should be False in International case.",
        )
