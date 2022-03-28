# Copyright 2021 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from erpbrasil.base.fiscal.cnpj_cpf import validar_cnpj
from erpbrasil.base.misc import punctuation_rm
from requests import get

from odoo import _, api, models
from odoo.exceptions import ValidationError


class PartyMixin(models.AbstractModel):
    _inherit = "l10n_br_base.party.mixin"

    @api.onchange("cnpj_cpf")
    def _onchange_cnpj_cpf(self):
        result = super()._onchange_cnpj_cpf()
        cnpj_cpf = punctuation_rm(self.cnpj_cpf)
        if cnpj_cpf and validar_cnpj(cnpj_cpf):
            response = get("https://www.receitaws.com.br/v1/cnpj/" + cnpj_cpf)
            try:
                data = response.json()
            except ValueError:
                raise ValidationError(_("Não foi possível conectar ao receitaws."))

            if data.get("status") == "ERROR":
                raise ValidationError(_(data.get("message")))

            self.company_type = "company"
            self.legal_name = self.get_field(data, "nome", title=True)
            fantasy_name = self.get_field(data, "fantasia", title=True)
            self.name = fantasy_name if fantasy_name else self.legal_name
            self.email = self.get_field(data, "email", lower=True)
            self.street = self.get_field(data, "logradouro", title=True)
            self.street2 = self.get_field(data, "complemento", title=True)
            self.district = self.get_field(data, "bairro", title=True)
            self.street_number = self.get_field(data, "numero")
            self.zip = self.get_field(data, "cep")
            self.get_phones(data)
            self.get_state_city(data)

        return result

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
    def get_field(data, name, title=False, lower=False):
        value = False
        if data.get(name) != "":
            value = data[name]
            if lower:
                value = value.lower()
            elif title:
                value = value.title()

        return value
