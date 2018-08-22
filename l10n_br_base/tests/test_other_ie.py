# -*- coding: utf-8 -*-
# @ 2018 Akretion - www.akretion.com.br -
#   Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo.tests.common import TransactionCase

import logging

_logger = logging.getLogger(__name__)


class OtherIETest(TransactionCase):

    def setUp(self):
        super(OtherIETest, self).setUp()
        self.company_model = self.env['res.company']
        self.company = self.company_model.create({
            'name': 'Akretion Sao Paulo',
            'legal_name': 'Akretion Sao Paulo',
            'cnpj_cpf': '26.905.703/0001-52',
            'inscr_est': '932.446.119.086',
            'street': 'Rua Paulo Dias',
            'number': '586',
            'district': 'Alumínio',
            'state_id': self.ref('base.state_br_sp'),
            'l10n_br_city_id': self.ref('l10n_br_base.city_3501152'),
            'country_id': self.ref('base.br'),
            'city': 'Alumínio',
            'zip': '18125-000',
            'phone': '+55 (21) 3010 9965',
            'email': 'contact@companytest.com.br',
            'website': 'www.companytest.com.br'
        })

    def test_included_valid_ie_in_company(self):
        result = self.company.write({
            'other_inscr_est_lines': [(0, 0, {
                'state_id': self.ref('base.state_br_ba'),
                'inscr_est': 41902653,
            })]
        })
        self.assertTrue(result, "Error to included valid IE.")
        for line in self.company.partner_id.other_inscr_est_lines:
            result = False
            if line.inscr_est == '41902653':
                result = True
            self.assertTrue(
                result, "Error in method to update other IE(s) on partner.")

        try:
            result = self.company.write({
                'other_inscr_est_lines': [(0, 0, {
                    'state_id': self.ref('base.state_br_ba'),
                    'inscr_est': 67729139,
                })]
            })
        except:
            result = False

        self.assertFalse(
            result, "Error to check included other"
                    " IE to State already informed.")

    def test_included_invalid_ie(self):
        try:
            result = self.company.write({
                'other_inscr_est_lines': [(0, 0, {
                    'state_id': self.ref('base.state_br_ba'),
                    'inscr_est': 41902652,
                })]
            })
        except:
            result = False
        self.assertFalse(result, "Error to check included invalid IE.")

    def test_included_other_valid_ie_to_same_state_of_company(self):
        try:
            result = self.company.write({
                'other_inscr_est_lines': [(0, 0, {
                    'state_id': self.ref('base.state_br_sp'),
                    'inscr_est': 692015742119,
                })]
            })
        except:
            result = False
        self.assertFalse(
            result, "Error to check included other valid IE "
                    " in to same state of Company.")

    def test_included_valid_ie_on_partner(self):
        result = self.company.partner_id.write({
            'other_inscr_est_lines': [(0, 0, {
                'state_id': self.ref('base.state_br_ba'),
                'inscr_est': 41902653,
            })]
        })
        self.assertTrue(result, "Error to included valid IE.")
        for line in self.company.other_inscr_est_lines:
            result = False
            if line.inscr_est == '41902653':
                result = True
            self.assertTrue(
                result, "Error in method to update other IE(s) on Company.")
