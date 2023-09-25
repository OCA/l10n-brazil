# Copyright 2022 KMEE - Luis Felipe Mileo
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from os.path import dirname

from odoo import api, models

_logger = logging.getLogger(__name__)

SERPRO_URL = "https://gateway.apiserpro.serpro.gov.br"

QUALIFICACAO_CSV = dirname(__file__) + "/../data/serpro_qualificacao.csv"


class SerproWebserviceCRM(models.AbstractModel):
    _inherit = "l10n_br_cnpj_search.webservice.abstract"

    @api.model
    def _serpro_import_data(self, data):
        schema = self._get_cnpj_param("serpro_schema")

        legal_name = self.get_data(data, "nomeEmpresarial", title=True)
        fantasy_name = self.get_data(data, "nomeFantasia", title=True)
        name = fantasy_name if fantasy_name else legal_name
        phone, mobile = self._serpro_get_phones(data)
        address = data.get("endereco")
        data.get("naturezaJuridica")
        cep = self.get_data(address, "cep")

        res = {
            "legal_name": legal_name,
            "name": name,
            "street_name": self.get_data(address, "logradouro", title=True),
            "street2": self.get_data(address, "complemento", title=True),
            "district": self.get_data(address, "bairro", title=True),
            "street_number": self.get_data(address, "numero"),
            "zip": cep,
            "phone": phone,
            "mobile": mobile,
            "state_id": self._get_state_id(address),
            "city_id": self._get_city_id(cep),
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

            values = {"name": partner_name, "function": partner_qualification}

            if schema == "empresa":
                partner_cpf = self.get_data(partner, "cpf")
                values.update({"cnpj_cpf": partner_cpf})

            partner_id = self.env["res.partner"].create(values).id
            child_ids.append(partner_id)

        return {
            "child_ids": [(6, 0, child_ids)],
        }
