# Copyright 2019 Akretion - Renato Lima <renato.lima@akretion.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from dateutil.relativedelta import relativedelta

from odoo import fields
from odoo.tests import SavepointCase


class TestCurrencyRateUpdateBCB(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Company = cls.env["res.company"]
        cls.CurrencyRate = cls.env["res.currency.rate"]
        cls.CurrencyRateProvider = cls.env["res.currency.rate.provider"]

        cls.today = fields.Date.today()
        cls.brl_currency = cls.env.ref("base.BRL")
        cls.brl_currency.write({"active": True})
        cls.eur_currency = cls.env.ref("base.EUR")
        cls.usd_currency = cls.env.ref("base.USD")
        cls.usd_currency.write({"active": True})
        cls.company = cls.Company.create(
            {"name": "Test company BRL", "currency_id": cls.brl_currency.id}
        )
        cls.env.user.company_ids += cls.company
        cls.env.user.company_id = cls.company
        cls.bcb_provider = cls.CurrencyRateProvider.create(
            {
                "service": "BCB",
                "currency_ids": [
                    (4, cls.usd_currency.id),
                    (4, cls.eur_currency.id),
                ],
            }
        )
        cls.CurrencyRate.search([]).unlink()

    def test_get_supported_currencies(self):
        currencies = self.bcb_provider._get_supported_currencies()
        self.assertTrue(currencies)

    def test_update_BCB_today(self):
        """No checks are made since today may not be a banking day"""
        self.bcb_provider._update(self.today, self.today)
        self.CurrencyRate.search([("currency_id", "=", self.usd_currency.id)]).unlink()

    def test_update_BCB_month(self):
        self.bcb_provider._update(self.today - relativedelta(months=1), self.today)

        rates = self.CurrencyRate.search(
            [("currency_id", "=", self.usd_currency.id)], limit=1
        )
        self.assertTrue(rates)

        self.CurrencyRate.search([("currency_id", "=", self.usd_currency.id)]).unlink()

    def test_update_BCB_year(self):
        self.bcb_provider._update(self.today - relativedelta(years=1), self.today)

        rates = self.CurrencyRate.search(
            [("currency_id", "=", self.usd_currency.id)], limit=1
        )
        self.assertTrue(rates)

        self.CurrencyRate.search([("currency_id", "=", self.usd_currency.id)]).unlink()

    def test_update_BCB_scheduled(self):
        self.bcb_provider.interval_type = "days"
        self.bcb_provider.interval_number = 14
        self.bcb_provider.next_run = self.today - relativedelta(days=1)
        self.bcb_provider._scheduled_update()

        rates = self.CurrencyRate.search(
            [("currency_id", "=", self.usd_currency.id)], limit=1
        )
        self.assertTrue(rates)

        self.CurrencyRate.search([("currency_id", "=", self.usd_currency.id)]).unlink()

    def test_update_BCB_no_base_update(self):
        self.bcb_provider.interval_type = "days"
        self.bcb_provider.interval_number = 14
        self.bcb_provider.next_run = self.today - relativedelta(days=1)
        self.bcb_provider._scheduled_update()

        rates = self.CurrencyRate.search(
            [
                ("company_id", "=", self.company.id),
                (
                    "currency_id",
                    "in",
                    [self.usd_currency.id, self.eur_currency.id],
                ),
            ],
            limit=1,
        )
        self.assertTrue(rates)

        self.CurrencyRate.search([("company_id", "=", self.company.id)]).unlink()
