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
            ]

        return super()._get_supported_currencies()

    @api.model
    def _obtain_rates(self, base_currency, currencies, date_from, date_to):
        self.ensure_one()
        if self.service == "BCB":
            if base_currency != "BRL":
                raise UserError(
                    _(
                        "Brazilian Central Bank is suitable only for companies"
                        " with BRL as base currency!"
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
                params["@moeda"] = "'" + cur + "'"
                response = requests.get(url, params=params)
                if response.ok:
                    content = response.json()

                    for rate in content.get("value"):
                        rate_date = fields.Date.from_string(
                            rate.get("dataHoraCotacao")
                        ).strftime(DEFAULT_SERVER_DATE_FORMAT)

                        if data.get(rate_date):
                            data[rate_date][cur] = 1 / rate.get("cotacaoVenda")
                        else:
                            rate_dict = {cur: 1 / rate.get("cotacaoVenda")}
                            data[rate_date] = rate_dict

            return data

        return super()._obtain_rates(base_currency, currencies, date_from, date_to)
