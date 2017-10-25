# -*- coding: utf-8 -*-
# @ 2017 Akretion - www.akretion.com.br -
#   Clément Mombereau <clement.mombereau@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests.common import TransactionCase


class CrmLeadTest(TransactionCase):
    """Test basic operations on Lead"""

    def setUp(self):
        super(CrmLeadTest, self).setUp()

        # Create lead with simple details
        self.crm_lead_company = self.env['crm.lead'].create({
            'name': 'Test Company Lead',
            'legal_name': 'Teste Empresa',
            'cnpj': '56.647.352/0001-98',
            'stage_id': self.env.ref('crm.stage_lead1').id,
            'partner_name': 'Test Partner',
            'inscr_est': '079.798.013.363',
            'inscr_mun': '99999999'
            })

        # Create lead for a person/contact
        self.crm_lead_contact = self.env['crm.lead'].create({
            'name': 'Test Contact',
            'cpf': '70531160505',
            'rg': '99.888.777-1',
            'stage_id': self.env.ref('crm.stage_lead1').id,
            'partner_name': 'Test Contact',
            })

        # Create lead with a valid Inscr. Estadual
        self.crm_lead_company_1 = self.env['crm.lead'].create({
            'name': 'Test Company Lead IE',
            'legal_name': 'Teste Empresa 1',
            'cnpj': '57.240.310/0001-09',
            'stage_id': self.env.ref('crm.stage_lead1').id,
            'partner_name': 'Test Partner 1',
            'inscr_est': '041.092.540.590',
            'inscr_mun': '99999999',
            'country_id': self.env.ref('base.br').id,
            'state_id': self.env.ref('base.state_br_sp').id
            })

    # Tests on crm_lead_company

    def test_lead_lost(self):
        """Test to mark the Lead as lost"""
        self.crm_lead_company.case_mark_lost()

    def test_conversion(self):
        """Test to convert a Lead"""
        # Set lead to Open stage
        self.crm_lead_company.write({
            'stage_id': self.env.ref('crm.stage_lead1').id
            })
        # Check if the lead stage is "Open".
        self.assertEqual(
            self.crm_lead_company.stage_id.sequence, 1,
            'Lead stage did not Open')
        # Convert lead into opportunity for exiting customer
        self.crm_lead_company.convert_opportunity(
            self.env.ref("base.res_partner_2").id)

        # Check details of converted opportunity
        self.assertEqual(
            self.crm_lead_company.type, 'opportunity',
            'Lead is not converted to opportunity!')
        self.assertEqual(
            self.crm_lead_company.partner_id.id,
            self.env.ref("base.res_partner_2").id, 'Partner mismatch!')
        self.assertEqual(
            self.crm_lead_company.stage_id.id,
            self.env.ref("crm.stage_lead1").id,
            'Stage of opportunity is incorrect!')

    def test_create_partner(self):
        """ Create a Partner and check the if the fields were filled """
        self.partner_id = self.env['crm.lead']._create_lead_partner(
            self.crm_lead_company)

        self.obj_partner = self.env['res.partner'].browse(
            self.partner_id)

        self.assertTrue(self.obj_partner.name,
                        'The creation of the partner have problems.')
        self.assertTrue(self.obj_partner.legal_name,
                        'The field Razão Social not was filled.')
        self.assertTrue(self.obj_partner.cnpj_cpf,
                        'The field CNPJ not was filled.')
        self.assertTrue(self.obj_partner.inscr_est,
                        'The field Inscrição Estadual not was filled')
        self.assertTrue(self.obj_partner.inscr_mun,
                        'The field Inscrição Municipal not was filled')

# TODO fix up .case_mark_won()
    def test_lead_won(self):
        """Test to mark the Lead as won"""
        # self.crm_lead_company.case_mark_won()

    # Tests on crm_lead_contact

    def test_lead_lost_contact(self):
        """Test to mark the Lead as lost"""
        self.crm_lead_contact.case_mark_lost()

    def test_conversion_contact(self):
        """Test to convert a Lead"""
        # Set lead to Open stage
        self.crm_lead_contact.write({
            'stage_id': self.env.ref('crm.stage_lead1').id
            })
        # Check if the lead stage is "Open".
        self.assertEqual(
            self.crm_lead_contact.stage_id.sequence, 1,
            'Lead stage did not Open')
        # Convert lead into opportunity for exiting customer
        self.crm_lead_contact.convert_opportunity(
            self.env.ref("base.res_partner_2").id)

        # Check details of converted opportunity
        self.assertEqual(
            self.crm_lead_contact.type, 'opportunity',
            'Lead is not converted to opportunity!')
        self.assertEqual(
            self.crm_lead_contact.partner_id.id,
            self.env.ref("base.res_partner_2").id, 'Partner mismatch!')
        self.assertEqual(
            self.crm_lead_contact.stage_id.id,
            self.env.ref("crm.stage_lead1").id,
            'Stage of opportunity is incorrect!')

    def test_create_contact(self):
        """ Create a Contact and check the if the fields were filled """
        self.partner_id = self.env['crm.lead']._create_lead_partner(
            self.crm_lead_contact)
        self.obj_partner = self.env['res.partner'].browse(self.partner_id)

        self.assertTrue(self.obj_partner.name,
                        'The creation of the partner have problems.')

# TODO CPF and RG not found. In :
    # self.assertTrue(self.obj_partner.cnpj_cpf, ...)
    # and
    # self.assertTrue(self.obj_partner.inscr_est, ...)
#
# `self.obj_partner.cnpj_cpf` and `self.obj_partner.inscr_est` are False.
# Problem when testing in the interface, when creating a partner from a lead,
# only the name is recorded, the CPF and RG are lost.
#

# TODO fix up .case_mark_won()
    def test_lead_won_contact(self):
        """Test to mark the Lead as won"""
        # self.crm_lead_company.case_mark_won()

    # Tests on crm_lead_company_1

    def test_create_partner_IE(self):
        """
        Create a partner of crm_lead_company_1 and
        check if the fields were fields with Inscr. Estadual ok
        """
        self.partner_id = self.env['crm.lead']._create_lead_partner(
            self.crm_lead_company_1)

        self.obj_partner = self.env['res.partner'].browse(
            self.partner_id)

        self.assertTrue(self.obj_partner.name,
                        'The creation of the partner have problems.')
        self.assertTrue(self.obj_partner.legal_name,
                        'The field Razão Social not was filled.')
        self.assertTrue(self.obj_partner.cnpj_cpf,
                        'The field CNPJ not was filled.')
        self.assertTrue(self.obj_partner.inscr_est,
                        'The field Inscrição Estadual not was filled')
        self.assertTrue(self.obj_partner.inscr_mun,
                        'The field Inscrição Municipal not was filled')
        self.assertTrue(self.obj_partner.country_id,
                        'The field Country not was filled')
        self.assertTrue(self.obj_partner.state_id,
                        'The field State not was filled')
