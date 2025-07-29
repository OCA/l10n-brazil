# Copyright 2019 Akretion - Renato Lima <renato.lima@akretion.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import requests

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT


class ResCurrencyRateProviderBCB(models.Model):
    _inherit = "res.currency.rate.provider"

    service = fields.Selection(
        selection_add=[("BCB", "Brazilian Central Bank")],
        ondelete={"BCB": "set default"},
    )

    @api.model
    def _get_supported_currencies(self):
        self.ensure_one()
        if self.service == "BCB":
            # List of currencies obrained from:
            # https://olinda.bcb.gov.br/olinda/servico/PTAX/versao
            # /v1/odata/Moedas?$top=100&$format=json&$select=simbolo
            return [
                "AUD",
                "CAD",
                "CHF",
                "DKK",
                "EUR",
                "GBP",
                "JPY",
                "NOK",
                "SEK",
                "USD",
                "BRL",
            ]

        return super()._get_supported_currencies()

    @api.model
    def _obtain_rates(self, base_currency, currencies, date_from, date_to):
        self.ensure_one()
        if self.service == "BCB":
            if base_currency != "BRL" and "BRL" not in currencies:
                raise UserError(
                    _(
                        "Brazilian Central Bank can only provide rates for"
                        " conversions involving BRL!"
                    )
                )

            url = (
                "https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/"
                "v1/odata/CotacaoMoedaPeriodo(moeda=@moeda,dataInicial"
                "=@dataInicial,dataFinalCotacao=@dataFinalCotacao)?"
                "format=json&skip=0&top=10000&$filter=tipoBoletim%20eq"
                "%20%27Fechamento%27%20or%20tipoBoletim%20eq%20%27Abert"
                "ura%27&select=paridadeCompra%2CparidadeVen"
                "da%2CcotacaoCompra%2CcotacaoVenda%2CdataHoraCotacao%2"
                "CtipoBoletim"
            )

            params = dict()
            params["@dataInicial"] = date_from.strftime("'%m-%d-%Y'")
            params["@dataFinalCotacao"] = date_to.strftime("'%m-%d-%Y'")

            data = {}
            for cur in currencies:
                if cur == base_currency:
                    continue

                params["@moeda"] = "'" + cur + "'"
                response = requests.get(url, params=params, timeout=10)
                if response.ok:
                    content = response.json()

                    for rate in content.get("value"):
                        rate_date = fields.Date.from_string(
                            rate.get("dataHoraCotacao")
                        ).strftime(DEFAULT_SERVER_DATE_FORMAT)

                        cotacao_venda = rate.get("cotacaoVenda")
                        if not cotacao_venda:
                            raise UserError(
                                _(
                                    "No exchange rate found for %(currency)s "
                                    "on %(date)s. Please check the BCB service."
                                )
                                % {"currency": cur, "date": rate_date}
                            )

                        if base_currency == "BRL":
                            rate_value = 1 / cotacao_venda
                            target_currency = cur
                        else:
                            rate_value = cotacao_venda
                            target_currency = "BRL"

                        if rate_date in data:
                            data[rate_date][target_currency] = rate_value
                        else:
                            data[rate_date] = {target_currency: rate_value}

            return data

        return super()._obtain_rates(base_currency, currencies, date_from, date_to)
