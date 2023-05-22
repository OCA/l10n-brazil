# Copyright 2022 KMEE - Luis Felipe Mileo
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import csv
import logging
from os.path import dirname

from odoo import models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

SERPRO_URL = "https://gateway.apiserpro.serpro.gov.br"

QUALIFICACAO_CSV = dirname(__file__) + "/../data/serpro_qualificacao.csv"


class SerproWebservice(models.Model):
    _inherit = "l10n_br_cnpj.webservice"

    def serpro_get_api_url(self, cnpj):
        trial = self._get_cnpj_param("serpro_trial")
        schema = self._get_cnpj_param("serpro_schema")

        if trial:
            url = SERPRO_URL + f"/consulta-cnpj-df-trial/v2/{schema}/{cnpj}"
        else:
            url = SERPRO_URL + f"/v2/{schema}/{cnpj}"  # TODO

        return url

    def serpro_get_headers(self):
        token = self._get_cnpj_param("serpro_token")
        return {"Authorization": "Bearer " + token}

    def serpro_validate(self, response):
        self._validate(response)
        data = response.json()
        return data

    def serpro_import_data(self, data):
        schema = self._get_cnpj_param("serpro_schema")

        legal_name = self.get_data(data, "nomeEmpresarial", title=True)
        fantasy_name = self.get_data(data, "nomeFantasia", title=True)
        name = fantasy_name if fantasy_name else legal_name
        phone, mobile = self.serpro_get_phones(data)
        endereco = data.get("endereco")
        cep = self.get_data(endereco, "cep")
        state_id = self.get_state_id(endereco)
        city_id = self.get_city_id(cep)
        capital_social = self.get_data(data, "capitalSocial")
        cnae_id = self.serpro_get_cnae(data)

        res = {
            "legal_name": legal_name,
            "name": name,
            "email": self.get_data(data, "correioEletronico"),
            "street_name": self.get_data(endereco, "logradouro", title=True),
            "street2": self.get_data(endereco, "complemento", title=True),
            "district": self.get_data(endereco, "bairro", title=True),
            "street_number": self.get_data(endereco, "numero"),
            "zip": cep,
            "phone": phone,
            "mobile": mobile,
            "state_id": state_id,
            "city_id": city_id,
            "capital_social": capital_social,
            "cnae_main_id": cnae_id,
        }

        res.update(self.import_additional_info(data, schema))

        return res

    def import_additional_info(self, data, schema):
        if schema not in ["empresa", "qsa"]:
            return {}

        socios = data.get("socios")
        child_ids = []
        for socio in socios:
            socio_name = self.get_data(socio, "nome", title=True)
            socio_qualification = self.get_qualification(socio)

            values = {
                "name": socio_name,
                "function": socio_qualification,
                "company_type": "person",
            }

            if schema == "empresa":
                socio_cpf = self.get_data(socio, "cpf")
                values.update({"cnpj_cpf": socio_cpf})

            socio_id = self.env["res.partner"].create(values).id
            child_ids.append(socio_id)

        return {
            "child_ids": [(6, 0, child_ids)],
        }

    def get_qualification(self, socio):
        qualification = self.get_data(socio, "qualificacao")

        with open(QUALIFICACAO_CSV) as csvfile:
            reader = csv.reader(csvfile, delimiter=",")
            next(reader)  # Remove header
            for row in reader:
                if row[0] == qualification:
                    return row[1]
        return ""

    @staticmethod
    def serpro_get_phones(data):
        """Get phones from data.
        If there is more than one phone, the second is assigned to mobile and the rest
        is ignored."""
        phones = []
        phones_data = data.get("telefones")
        for i in range(min(len(phones_data), 2)):
            ddd = phones_data[i].get("ddd")
            num = phones_data[i].get("numero")
            phone = f"({ddd}) {num}"

            phones.append(phone)

        return phones

    def get_state_id(self, endereco):
        state_code = self.get_data(endereco, "uf")

        return (
            self.env["res.country.state"]
            .search(
                [("country_id.code", "=", "BR"), ("code", "=", state_code)], limit=1
            )
            .id
        )

    def get_city_id(self, cep):
        # Get city from cep
        # TODO Send message if address doesn't match CEP
        try:
            cep_values = self.env["l10n_br.zip"]._consultar_cep(cep)
        except UserError as error:
            _logger.warning(error.name)
            return False

        return cep_values.get("city_id")

    def serpro_get_cnae(self, data):
        cnae_main = data.get("cnaePrincipal")
        cnae_code = self.get_data(cnae_main, "codigo")

        return self._get_cnae(cnae_code)
