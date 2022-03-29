# Copyright 2021 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from erpbrasil.base.misc import punctuation_rm
from requests import get

from odoo import _, models
from odoo.exceptions import UserError, ValidationError

RECEITAWS_URL = "https://www.receitaws.com.br/v1/cnpj/"


class PartyMixin(models.AbstractModel):
    _inherit = "l10n_br_base.party.mixin"

    def search_cnpj(self):
        """Search CNPJ by the chosen API.
        This method doesn't need to validate the CNPJ since it's already validated on
        the onchange method.
        """
        if not self.cnpj_cpf:
            raise UserError(_("Por favor insira o CNPJ"))

        cnpj_cpf = punctuation_rm(self.cnpj_cpf)
        response = get(RECEITAWS_URL + cnpj_cpf)
        try:
            data = response.json()
        except ValueError:
            raise ValidationError(_("Não foi possível conectar ao receitaws."))

        if data.get("status") == "ERROR":
            raise ValidationError(_(data.get("message")))

        self.company_type = "company"
        self.legal_name = self.get_data(data, "nome", title=True)
        fantasy_name = self.get_data(data, "fantasia", title=True)
        self.name = fantasy_name if fantasy_name else self.legal_name
        self.email = self.get_data(data, "email", lower=True)
        self.street = self.get_data(data, "logradouro", title=True)
        self.street2 = self.get_data(data, "complemento", title=True)
        self.district = self.get_data(data, "bairro", title=True)
        self.street_number = self.get_data(data, "numero")
        self.zip = self.get_data(data, "cep")
        self.get_phones(data)
        self.get_state_city(data)

    def get_phones(self, data):
        if data.get("telefone") != "":
            phones = data["telefone"].split("/")
            self.phone = phones[0]
            if len(phones) > 1:
                self.mobile = phones[1][1:]  # Remove Empty space separation

    def get_state_city(self, data):
        if data.get("uf") != "":
            state_id = self.env["res.country.state"].search(
                [
                    ("code", "=", data["uf"]),
                    ("country_id", "=", self.country_id.id),
                ],
                limit=1,
            )
            self.state_id = state_id

            if data.get("municipio") != "":
                city_id = self.env["res.city"].search(
                    [
                        ("name", "=ilike", data["municipio"].title()),
                        ("state_id.id", "=", state_id.id),
                    ]
                )
                if len(city_id) == 1:
                    self.city_id = city_id

    @staticmethod
    def get_data(data, name, title=False, lower=False):
        value = False
        if data.get(name) != "":
            value = data[name]
            if lower:
                value = value.lower()
            elif title:
                value = value.title()

        return value
