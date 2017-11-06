# -*- coding: utf-8 -*-
# @ 2017 Akretion - www.akretion.com.br -
#   Clément Mombereau <clement.mombereau@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests.common import TransactionCase


class L10nBrCrmOnchangeTest(TransactionCase):

    def setUp(self):
        super(L10nBrCrmOnchangeTest, self).setUp()

        self.crm_lead_01 = self.env['crm.lead'].create({
            'name': 'Test Company Lead',
            'cnpj': '56.647.352/0001-98',
            'l10n_br_city_id': self.env.ref('l10n_br_base.city_3205002').id,
            'zip': '29161-695',
            'cpf': '70531160505',
            })

    def test_onchange(self):
        """
        Call all the onchange methods in l10n_br_crm
        """
        self.crm_lead_01._onchange_cnpj()
        self.crm_lead_01.onchange_mask_cpf()
        self.crm_lead_01.onchange_l10n_br_city_id()
        self.crm_lead_01._onchange_zip()

        self.crm_lead_01._create_lead_partner()
        self.crm_lead_01._onchange_partner_id()
