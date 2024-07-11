# pylint: disable=R8180
# Copyright 2022 KMEE - Luis Felipe Mileo
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import csv
import logging
from os.path import dirname

from odoo import api, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

SERPRO_URL = "https://gateway.apiserpro.serpro.gov.br"

QUALIFICACAO_CSV = dirname(__file__) + "/../data/serpro_qualificacao.csv"


class SerproWebservice(models.AbstractModel):
    _inherit = "l10n_br_cnpj_search.webservice.abstract"

    @api.model
    def serpro_get_api_url(self, cnpj):
        trial = self._get_cnpj_param("serpro_trial")
        schema = self._get_cnpj_param("serpro_schema")

        if trial:
            url = SERPRO_URL + f"/consulta-cnpj-df-trial/v2/{schema}/{cnpj}"
        else:
            url = SERPRO_URL + f"/v2/{schema}/{cnpj}"

        return url

    @api.model
    def serpro_get_headers(self):
        token = self._get_cnpj_param("serpro_token")
        return {"Authorization": "Bearer " + token}

    @api.model
    def serpro_validate(self, response):
        self._validate(response)
        data = response.json()
        return data

    @api.model
    def _serpro_import_data(self, data):
        schema = self._get_cnpj_param("serpro_schema")

        legal_name = self.get_data(data, "nomeEmpresarial", title=True)
        fantasy_name = self.get_data(data, "nomeFantasia", title=True)
        name = fantasy_name if fantasy_name else legal_name
        phone, mobile = self._serpro_get_phones(data)
        address = data.get("endereco")
        nature = data.get("naturezaJuridica")
        cep = self.get_data(address, "cep")

        res = {
            "legal_name": legal_name,
            "name": name,
            "email": self.get_data(data, "correioEletronico"),
            "street_name": self.get_data(address, "logradouro", title=True),
            "street2": self.get_data(address, "complemento", title=True),
            "district": self.get_data(address, "bairro", title=True),
            "street_number": self.get_data(address, "numero"),
            "legal_nature": self.get_data(nature, "codigo", title=True)
            + self.get_data(nature, "descricao", title=True),
            "zip": cep,
            "phone": phone,
            "mobile": mobile,
            "state_id": self._get_state_id(address),
            "city_id": self._get_city_id(cep),
            "equity_capital": self.get_data(data, "capitalSocial"),
            "cnae_main_id": self._serpro_get_cnae(data),
        }

        res.update(self._import_additional_info(data, schema))

        return res

    @api.model
    def _import_additional_info(self, data, schema):
        if schema not in ["empresa", "qsa"]:
            return {}

        partners = data.get("socios")
        child_ids = []
        for partner in partners:
            partner_name = self.get_data(partner, "nome", title=True)
            partner_qualification = self._get_qualification(partner)

            values = {
                "name": partner_name,
                "function": partner_qualification,
                "company_type": "person",
            }

            if schema == "empresa":
                partner_cpf = self.get_data(partner, "cpf")
                values.update({"cnpj_cpf": partner_cpf})

            partner_id = self.env["res.partner"].create(values).id
            child_ids.append(partner_id)

        return {
            "child_ids": [(6, 0, child_ids)],
        }

    @api.model
    def _get_qualification(self, partner):
        qualification = self.get_data(partner, "qualificacao")

        with open(QUALIFICACAO_CSV) as csvfile:
            reader = csv.reader(csvfile, delimiter=",")
            next(reader)  # Remove header
            for row in reader:
                if row[0] == qualification:
                    return row[1]
        return ""

    @api.model
    def _serpro_get_phones(self, data):
        """Get phones from data.
        If there is more than one phone, the second is assigned to mobile and the rest
        is ignored."""
        phone = False
        mobile = False
        phones_data = data.get("telefones")
        ddd = phones_data[0].get("ddd")
        num = phones_data[0].get("numero")
        phone = f"({ddd}) {num}"
        if len(phones_data) == 2:
            ddd = phones_data[1].get("ddd")
            num = phones_data[1].get("numero")
            mobile = f"({ddd}) {num}"

        return phone, mobile

    @api.model
    def _get_state_id(self, address):
        state_code = self.get_data(address, "uf")

        return (
            self.env["res.country.state"]
            .search(
                [("country_id.code", "=", "BR"), ("code", "=", state_code)], limit=1
            )
            .id
        )

    @api.model
    def _get_city_id(self, cep):
        # Get city from cep
        # TODO Send message if address doesn't match CEP
        try:
            cep_values = self.env["l10n_br.zip"]._consultar_cep(cep)
        except UserError as error:
            _logger.warning(error.name)
            return False

        return cep_values.get("city_id")

    @api.model
    def _serpro_get_cnae(self, data):
        cnae_main = data.get("cnaePrincipal")
        cnae_code = self.get_data(cnae_main, "codigo")

        return self._get_cnae(cnae_code)
