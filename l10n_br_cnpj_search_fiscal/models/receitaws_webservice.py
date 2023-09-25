# Copyright 2022 KMEE - Luis Felipe Mileo
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models

RECEITAWS_URL = "https://www.receitaws.com.br/v1/cnpj/"


class ReceitawsWebserviceFiscal(models.AbstractModel):
    _inherit = "l10n_br_cnpj_search.webservice.abstract"

    @api.model
    def receitaws_get_api_url(self, cnpj):
        return RECEITAWS_URL + cnpj

    @api.model
    def _receitaws_import_data(self, data):
        legal_name = self.get_data(data, "nome", title=True)
        fantasy_name = self.get_data(data, "fantasia", title=True)
        phone, mobile = self._receitaws_get_phones(data)
        state_id, city_id = self._get_state_city(data)

        res = {
            "legal_name": legal_name,
            "name": fantasy_name if fantasy_name else legal_name,
            "email": self.get_data(data, "email", lower=True),
            "street_name": self.get_data(data, "logradouro", title=True),
            "street2": self.get_data(data, "complemento", title=True),
            "district": self.get_data(data, "bairro", title=True),
            "street_number": self.get_data(data, "numero"),
            "zip": self.get_data(data, "cep"),
            "legal_nature": self.get_data(data, "natureza_juridica"),
            "phone": phone,
            "mobile": mobile,
            "state_id": state_id,
            "city_id": city_id,
            "equity_capital": self.get_data(data, "capital_social"),
            "cnae_main_id": self._receitaws_get_cnae(data),
            "cnae_secondary_ids": self._receitaws_get_secondary_cnae(data),
        }

        return res

    @api.model
    def _receitaws_get_cnae(self, data):
        cnae_main = data.get("atividade_principal")[0]
        cnae_code = self.get_data(cnae_main, "code")

        return self._get_cnae(cnae_code)

    @api.model
    def _receitaws_get_secondary_cnae(self, data):
        cnae_secondary = []
        for atividade in data.get("atividades_secundarias"):
            unformated = self.get_data(atividade, "code").split(".")
            formatted = ""
            for nums in unformated:
                for num in nums.split("-"):
                    formatted += num

            if self._get_cnae(formatted) is not False:
                cnae_secondary.append(self._get_cnae(formatted))

        return cnae_secondary
