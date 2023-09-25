# Copyright 2022 KMEE - Luis Felipe Mileo
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from os.path import dirname

from odoo import api, models

_logger = logging.getLogger(__name__)

SERPRO_URL = "https://gateway.apiserpro.serpro.gov.br"

QUALIFICACAO_CSV = dirname(__file__) + "/../data/serpro_qualificacao.csv"


class SerproWebserviceFiscal(models.AbstractModel):
    _inherit = "l10n_br_cnpj_search.webservice.abstract"

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
    def _serpro_get_cnae(self, data):
        cnae_main = data.get("cnaePrincipal")
        cnae_code = self.get_data(cnae_main, "codigo")

        return self._get_cnae(cnae_code)
