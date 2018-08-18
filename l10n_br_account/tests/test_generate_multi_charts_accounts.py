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
                country_id=self.env.ref('base.br').id,
                currency_id=self.env.ref('base.BRL').id,
                transfer_account_id=self.env.ref(
                    'l10n_br.transfer_account_id').id,
            ))

        self.account_chart_template_1 = self.env.ref(
            'l10n_br_account.l10n_br_account_chart_template_demo')

        self.wzd_account_multi_charts_accounts = self.env[
            'wizard.multi.charts.accounts'].create(
            dict(
                company_id=self.company_1.id,
                currency_id=self.env.ref('base.BRL').id,
                transfer_account_id=self.env.ref(
                    'l10n_br.transfer_account_id').id,
                code_digits=6,
                chart_template_id=self.account_chart_template_1.id,
            ))
        self.wzd_account_multi_charts_accounts.onchange_chart_template_id()

    def test_generate_multi_charts_accounts(self):

        self.wzd_account_multi_charts_accounts.execute()
