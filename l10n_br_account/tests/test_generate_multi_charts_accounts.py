# -*- coding: utf-8 -*-
# @ 2018 Akretion - www.akretion.com.br -
#   Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests.common import TransactionCase


class TestGenerateMultiChartsAccounts(TransactionCase):

    def setUp(self):
        super(TestGenerateMultiChartsAccounts, self).setUp()
        self.company_1 = self.env['res.company'].create(
            dict(
                name='Empresa TESTE',
                currency_id=self.env.ref('base.BRL').id
            ))
        self.account_id = self.env['account.account.template'].search([])[0]
        self.wzd_account_multi_charts_accounts = self.env[
            'wizard.multi.charts.accounts'].create(
            dict(
                company_id=self.company_1.id,
                currency_id=self.env.ref('base.BRL').id,
                transfer_account_id=self.account_id.id,
                code_digits=6,
            ))

    def test_generate_multi_charts_accounts(self):
        self.wzd_account_multi_charts_accounts.execute()
