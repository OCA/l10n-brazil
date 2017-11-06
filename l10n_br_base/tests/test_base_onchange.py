# -*- coding: utf-8 -*-
# @ 2017 Akretion - www.akretion.com.br -
#   Clément Mombereau <clement.mombereau@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests.common import TransactionCase


class L10nBrBaseOnchangeTest(TransactionCase):

    def setUp(self):
        super(L10nBrBaseOnchangeTest, self).setUp()

        self.company_01 = self.env['res.company'].create({
            'name': 'Company Test 1',
            'cnpj_cpf': '02.960.895/0001-31',
            'l10n_br_city_id': self.env.ref('l10n_br_base.city_3205002').id,
            'zip': '29161-695',
            })

        self.bank_01 = self.env['res.bank'].create({
            'name': 'Bank Test 1',
            'l10n_br_city_id': self.env.ref('l10n_br_base.city_3205002').id,
            'zip': '29161-695',
            })

        self.partner_01 = self.env['res.partner'].create({
            'name': 'Partner Test 01',
            'l10n_br_city_id': self.env.ref('l10n_br_base.city_3205002').id,
            'zip': '29161-695',
            })

    def test_onchange(self):
        """
        Call all the onchange methods in l10n_br_base
        """
        self.company_01._onchange_cnpj_cpf()
        self.company_01._onchange_l10n_br_city_id()
        self.company_01._onchange_zip()

        self.bank_01._onchange_l10n_br_city_id()
        self.bank_01._onchange_zip()

        self.partner_01._onchange_cnpj_cpf()
        self.partner_01._onchange_l10n_br_city_id()
        self.partner_01._onchange_zip()
