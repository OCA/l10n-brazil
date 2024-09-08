# Copyright 2019 Akretion - Renato Lima <renato.lima@akretion.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging
from datetime import datetime
from os import environ
from unittest import mock

from dateutil.relativedelta import relativedelta
from decorator import decorate

from odoo import fields
from odoo.tests import SavepointCase

_logger = logging.getLogger(__name__)


def _not_every_day_test(method, self, modulo=7, remaining=1):
    if datetime.now().day % modulo == remaining or environ.get("CI_FORCE_IBPT"):
        return method(self)
    else:
        return lambda: _logger.info(
            f"Skipping test today because datetime.now().day % {modulo} != {remaining}"
        )


def not_every_day_test(method):
    """
    Decorate test methods to query the Banco Do Brasil only
    1 day out of 7 and skip tests otherwise.
    Indeed the IBPT webservice often returns errors and it sucks
    to crash the entire l10n-brazil test suite because of this.
    the CI_FORCE_IBPT env var can be set to force the test anyhow.
    """
    return decorate(method, _not_every_day_test)


def mocked_requests_get(*args, **kwargs):
    class MockResponse:
        def __init__(self, json_data, status_code):
            self.json_data = json_data
            self.status_code = status_code

        def ok(self):
            return True

        def json(self):
            return self.json_data

    # the same as rates during 2 days:
    return MockResponse(
        {
            "value": [
                {
                    "paridadeCompra": 1.0,
                    "paridadeVenda": 1.0,
                    "cotacaoCompra": 4.9786,
                    "cotacaoVenda": 4.9792,
                    "dataHoraCotacao": "2023-05-29 10:10:20.119",
                    "tipoBoletim": "Abertura",
                },
                {
                    "paridadeCompra": 1.0,
                    "paridadeVenda": 1.0,
                    "cotacaoCompra": 4.9948,
                    "cotacaoVenda": 4.9954,
                    "dataHoraCotacao": "2023-05-29 13:10:18.54",
                    "tipoBoletim": "Fechamento",
                },
                {
                    "paridadeCompra": 1.0,
                    "paridadeVenda": 1.0,
                    "cotacaoCompra": 5.0497,
                    "cotacaoVenda": 5.0503,
                    "dataHoraCotacao": "2023-05-30 10:09:35.311",
                    "tipoBoletim": "Abertura",
                },
                {
                    "paridadeCompra": 1.0,
                    "paridadeVenda": 1.0,
                    "cotacaoCompra": 5.0587,
                    "cotacaoVenda": 5.0593,
                    "dataHoraCotacao": "2023-05-30 13:11:51.392",
                    "tipoBoletim": "Fechamento",
                },
            ]
        },
        200,
    )


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

    @mock.patch("requests.get", side_effect=mocked_requests_get)
    def test_mock(self, mock_get):
        self.bcb_provider._update(self.today - relativedelta(days=2), self.today)
        rates = self.CurrencyRate.search(
            [("currency_id", "=", self.usd_currency.id)], limit=1
        )
        self.assertTrue(rates)
        self.CurrencyRate.search([("currency_id", "=", self.usd_currency.id)]).unlink()

    @not_every_day_test
    def test_get_supported_currencies(self):
        currencies = self.bcb_provider._get_supported_currencies()
        self.assertTrue(currencies)

    @not_every_day_test
    def test_update_BCB_today(self):
        """No checks are made since today may not be a banking day"""
        self.bcb_provider._update(self.today, self.today)
        self.CurrencyRate.search([("currency_id", "=", self.usd_currency.id)]).unlink()

    @not_every_day_test
    def test_update_BCB_month(self):
        self.bcb_provider._update(self.today - relativedelta(months=1), self.today)

        rates = self.CurrencyRate.search(
            [("currency_id", "=", self.usd_currency.id)], limit=1
        )
        self.assertTrue(rates)

        self.CurrencyRate.search([("currency_id", "=", self.usd_currency.id)]).unlink()

    @not_every_day_test
    def test_update_BCB_year(self):
        self.bcb_provider._update(self.today - relativedelta(years=1), self.today)

        rates = self.CurrencyRate.search(
            [("currency_id", "=", self.usd_currency.id)], limit=1
        )
        self.assertTrue(rates)

        self.CurrencyRate.search([("currency_id", "=", self.usd_currency.id)]).unlink()

    @not_every_day_test
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

    @not_every_day_test
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
