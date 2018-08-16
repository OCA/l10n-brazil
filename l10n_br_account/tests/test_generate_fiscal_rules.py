# -*- coding: utf-8 -*-
# @ 2018 Akretion - www.akretion.com.br -
#   Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests.common import TransactionCase


class TestGenerateFiscalRules(TransactionCase):

    def setUp(self):
        super(TestGenerateFiscalRules, self).setUp()
        self.wzd_account_fiscal_position_rule = self.env[
            'wizard.account.fiscal.position.rule'].create(
            dict(
                company_id=self.env.ref('base.main_company').id,
            ))

    def test_generate_fiscal_rules(self):
        self.wzd_account_fiscal_position_rule.action_create()
