# Copyright 2022 KMEE - Luis Felipe Mileo
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, models
from odoo.exceptions import ValidationError

RECEITAWS_URL = "https://www.receitaws.com.br/v1/cnpj/"


class ReceitawsWebservice(models.AbstractModel):
    _inherit = "l10n_br_cnpj_search.webservice.abstract"

    @api.model
    def receitaws_get_api_url(self, cnpj):
        return RECEITAWS_URL + cnpj

    @api.model
    def receitaws_get_headers(self):
        return {"Accept": "application/json"}

    @api.model
    def receitaws_validate(self, response):
        self._validate(response)
        data = response.json()
        if data.get("status") == "ERROR":
            raise ValidationError(_(data.get("message")))

        return data

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
    def _receitaws_get_phones(self, data):
        """Get phones from data.
        If there is more than one phone, the second is assigned to mobile."""
        phone = False
        mobile = False
        if data.get("telefone"):
            phones = data["telefone"].split("/")
            phone = phones[0]
            if len(phones) > 1:
                mobile = phones[1][1:]  # Remove Empty space separation

        return [phone, mobile]

    @api.model
    def _get_state_city(self, data):
        state_id = False
        city_id = False
        if data.get("uf"):
            state = self.env["res.country.state"].search(
                [
                    ("code", "=", data["uf"]),
                    ("country_id.code", "=", "BR"),
                ],
                limit=1,
            )
            if state.id:
                state_id = state.id

            if data.get("municipio"):
                city = self.env["res.city"].search(
                    [
                        ("name", "=ilike", data["municipio"].title()),
                        ("state_id.id", "=", state_id),
                    ]
                )
                if len(city) == 1:
                    city_id = city.id

        return [state_id, city_id]

    @api.model
    def _receitaws_get_cnae(self, data):
        if data.get("atividade_principal"):
            cnae_main = data.get("atividade_principal")[0]
            cnae_code = self.get_data(cnae_main, "code")
            return self._get_cnae(cnae_code)
        return False

    @api.model
    def _receitaws_get_secondary_cnae(self, data):
        cnae_secondary = []
        for atividade in data.get("atividades_secundarias", []):
            unformated = self.get_data(atividade, "code").split(".")
            formatted = ""
            for nums in unformated:
                for num in nums.split("-"):
                    formatted += num

            if self._get_cnae(formatted) is not False:
                cnae_secondary.append(self._get_cnae(formatted))

        return cnae_secondary
