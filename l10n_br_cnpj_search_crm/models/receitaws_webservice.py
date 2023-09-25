# Copyright 2022 KMEE - Luis Felipe Mileo
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models

RECEITAWS_URL = "https://www.receitaws.com.br/v1/cnpj/"


class ReceitawsWebserviceCRM(models.AbstractModel):
    _inherit = "l10n_br_cnpj_search.webservice.abstract"

    @api.model
    def _receitaws_import_data(self, data):
        legal_name = self.get_data(data, "nome", title=True)
        fantasy_name = self.get_data(data, "fantasia", title=True)
        phone, mobile = self._receitaws_get_phones(data)
        state_id, city_id = self._get_state_city(data)

        res = {
            "legal_name": legal_name,
            "name": fantasy_name if fantasy_name else legal_name,
            "street_name": self.get_data(data, "logradouro", title=True),
            "street2": self.get_data(data, "complemento", title=True),
            "district": self.get_data(data, "bairro", title=True),
            "street_number": self.get_data(data, "numero"),
            "zip": self.get_data(data, "cep"),
            "phone": phone,
            "mobile": mobile,
            "state_id": state_id,
            "city_id": city_id,
        }

        return res
