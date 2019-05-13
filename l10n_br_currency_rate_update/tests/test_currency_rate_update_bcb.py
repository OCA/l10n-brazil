# Copyright 2019 Akretion - Renato Lima <renato.lima@akretion.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from dateutil.relativedelta import relativedelta

from odoo.tests import common
from odoo import fields


class TestCurrencyRateUpdateBCB(common.TransactionCase):

    def setUp(self):
        super().setUp()

        self.Company = self.env['res.company']
        self.CurrencyRate = self.env['res.currency.rate']
        self.CurrencyRateProvider = self.env['res.currency.rate.provider']

        self.today = fields.Date.today()
        self.brl_currency = self.env.ref('base.BRL')
        self.brl_currency.write({'active': True})
        self.eur_currency = self.env.ref('base.EUR')
        self.usd_currency = self.env.ref('base.USD')
        self.usd_currency.write({'active': True})
        self.company = self.Company.create({
            'name': 'Test company BRL',
            'currency_id': self.brl_currency.id,
        })
        self.env.user.company_ids += self.company
        self.env.user.company_id = self.company
        self.bcb_provider = self.CurrencyRateProvider.create({
            'service': 'BCB',
            'currency_ids': [
                (4, self.usd_currency.id),
                (4, self.eur_currency.id),
            ],
        })
        self.CurrencyRate.search([]).unlink()

    def test_get_supported_currencies(self):
        currencies = self.bcb_provider._get_supported_currencies()
        self.assertTrue(currencies)

    def test_update_BCB_today(self):
        """No checks are made since today may not be a banking day"""
        self.bcb_provider._update(self.today, self.today)
        self.CurrencyRate.search([
            ('currency_id', '=', self.usd_currency.id),
        ]).unlink()

    def test_update_BCB_month(self):
        self.bcb_provider._update(
            self.today - relativedelta(months=1),
            self.today)

        rates = self.CurrencyRate.search([
            ('currency_id', '=', self.usd_currency.id)],
            limit=1)
        self.assertTrue(rates)

        self.CurrencyRate.search([
            ('currency_id', '=', self.usd_currency.id),
        ]).unlink()

    def test_update_BCB_year(self):
        self.bcb_provider._update(
            self.today - relativedelta(years=1),
            self.today
        )

        rates = self.CurrencyRate.search([
            ('currency_id', '=', self.usd_currency.id)],
            limit=1)
        self.assertTrue(rates)

        self.CurrencyRate.search([
            ('currency_id', '=', self.usd_currency.id),
        ]).unlink()

    def test_update_BCB_scheduled(self):
        self.bcb_provider.next_run = (
            fields.Date.today() - relativedelta(days=15)
        )
        self.bcb_provider._scheduled_update()

        rates = self.CurrencyRate.search([
            ('currency_id', '=', self.usd_currency.id),
        ], limit=1)
        self.assertTrue(rates)

        self.CurrencyRate.search([
            ('currency_id', '=', self.usd_currency.id),
        ]).unlink()

    def test_update_BCB_no_base_update(self):
        self.bcb_provider.next_run = (
            fields.Date.today() - relativedelta(days=15)
        )
        self.bcb_provider._scheduled_update()

        rates = self.CurrencyRate.search([
            ('company_id', '=', self.company.id),
            ('currency_id', 'in', [
                self.usd_currency.id,
                self.eur_currency.id]),
        ], limit=1)
        self.assertTrue(rates)

        self.CurrencyRate.search([
            ('company_id', '=', self.company.id),
        ]).unlink()
