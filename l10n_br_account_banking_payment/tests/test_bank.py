# -*- coding: utf-8 -*-
# @ 2018 Akretion - www.akretion.com.br -
#   Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)


import openerp.tests.common as common
import logging

_logger = logging.getLogger(__name__)


class TestBank(common.TransactionCase):

    def setUp(self):
        super(TestBank, self).setUp()
        self.model_res_bank = self.env['res.bank']
        self.model_res_partner_bank = self.env['res.partner.bank']
        self.model_partner = self.env['res.partner']
        self.bank_1 = self.model_res_bank.create({
            'bic': '001',
            'name': 'BANCO DO BRASIL S.A.',
            'country': self.ref('base.br'),
        })
        self.partner_1 = self.model_partner.create({
            'name': 'Akretion Sao Paulo',
            'is_company': True,
            'legal_name': 'Akretion Sao Paulo',
            'cnpj_cpf': '26.905.703/0001-52',
            'inscr_est': '932.446.119.086',
            'street': 'Rua Paulo Dias',
            'number': '586',
            'district': 'Alumínio',
            'state_id': self.ref('l10n_br_base.br_sp'),
            'l10n_br_city_id': self.ref('l10n_br_base.city_3501152'),
            'country_id': self.ref('base.br'),
            'city': 'Alumínio',
            'zip': '18125-000',
            'phone': '+55 (21) 3010 9965',
            'email': 'contact@companytest.com.br',
        })

    # TODO - https://github.com/OCA/l10n-brazil/issues/588
    def test_res_bank_bic(self):
        try:
            res_bank = self.model_res_bank.search([('id', '=', 1)])
            result = res_bank.write({'bic': '123456'})
        except:
            result = False
        self.assertFalse(result, "Error to included invalid BIC in Bank.")

    # TODO - https://github.com/OCA/l10n-brazil/issues/588
    def test_res_bank_bic_br(self):
        res_bank_br = self.model_res_bank.search(
            [('country_id.code', '=', 'BR')])[0]
        result = res_bank_br.write({'bic': '123456'})
        self.assertTrue(
            result, "Error to included invalid BIC in Brazil Bank.")

    # TODO - https://github.com/OCA/l10n-brazil/issues/588
    def test_res_partner_bank_bic(self):
        try:
            res_partner_bank = self.model_res_partner_bank.search(
                [('id', '=', 1)])
            result = res_partner_bank.write({'bank_bic': '123456'})
        except:
            result = False
        self.assertFalse(
            result, "Error to included invalid BIC in Partner Bank.")

    # TODO - https://github.com/OCA/l10n-brazil/issues/588
    def test_res_partner_bank_bic_br(self):
        result = self.model_res_partner_bank.create({
            'partner_id': self.partner_1.id,
            'state': 'bank',
            'acc_number': '1',
            'acc_number_dig': '1',
            'bra_number': '1',
            'bra_number_dig': '1',
            'bank': self.bank_1.id,
            'bank_bic': '123456',
        })
        self.assertTrue(
            result, "Error to included invalid BIC in Brazil Partner Bank.")
