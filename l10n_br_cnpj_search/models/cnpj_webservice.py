# Copyright 2022 KMEE - Luis Felipe Mileo
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import csv
import logging
from os.path import dirname

from erpbrasil.base.misc import punctuation_rm

from odoo import Command, _, api, models
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)

RECEITAWS_URL = "https://www.receitaws.com.br/v1/cnpj/"

SERPRO_URL = "https://gateway.apiserpro.serpro.gov.br"
QUALIFICACAO_CSV = dirname(__file__) + "/../data/serpro_qualificacao.csv"


class CNPJWebservice(models.AbstractModel):
    """Each specific webservice can extend the model by adding
    its own methods, using the webservice name (same as selection in config)
    as a prefix for the new methods.

    Methods that should be added in a webservice-specific implementation:
        - <name>_get_api_url(self, cnpj)
        - <name>_get_api_headers(self)
        - <name>_validate(self, response)
        - <name>_import_data(self, data)
    """

    _name = "l10n_br_cnpj_search.webservice.abstract"
    _description = "CNPJ Webservice"

    @api.model
    def get_provider(self):
        """Return selected provider in config"""
        if (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("l10n_br_cnpj_search.cnpj_provider")
        ):
            return (
                self.env["ir.config_parameter"]
                .sudo()
                .get_param("l10n_br_cnpj_search.cnpj_provider")
            )
        else:
            return "receitaws"

    @api.model
    def get_api_url(self, cnpj):
        """Get webservice endpoint

        Params:
            cnpj (str): Partner CNPJ.
        """
        if hasattr(self, "%s_get_api_url" % self.get_provider()):
            return getattr(self, "%s_get_api_url" % self.get_provider())(cnpj)
        return False

    @api.model
    def get_headers(self):
        """Get webservice request headers"""
        if hasattr(self, "%s_get_headers" % self.get_provider()):
            return getattr(self, "%s_get_headers" % self.get_provider())()
        return False

    @api.model
    def validate(self, response):
        """Validate webservice response.

        Returns: data (dict)
        """
        if hasattr(self, "%s_validate" % self.get_provider()):
            return getattr(self, "%s_validate" % self.get_provider())(response)
        return False

    @api.model
    def import_data(self, data):
        """Import webservice response to Odoo

        Params:
            data (dict): data with webservice response

        Returns:
            values (dict): dict with res_partner fields and it's values
        """
        if hasattr(self, "_%s_import_data" % self.get_provider()):
            return getattr(self, "_%s_import_data" % self.get_provider())(data)
        return False

    @api.model
    def get_data(self, data, name, title=False, lower=False):
        value = False
        if data.get(name) != "":
            value = data[name]
            if lower:
                value = value.lower()
            elif title:
                value = value.title()

        return value

    @api.model
    def _get_cnpj_param(self, param_name):
        return (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("l10n_br_cnpj_search." + param_name)
        )

    @api.model
    def _validate(self, response):
        if response.status_code != 200:
            raise ValidationError(_("%s") % response.reason)

    @api.model
    def _get_legal_nature(self, raw_code):
        code = punctuation_rm(raw_code)
        legal_nature_id = False
        if code:
            legal_nature_id = (
                self.env["l10n_br_fiscal.legal.nature"]
                .search([("code_unmasked", "=", code)])
                .id
            )
        return legal_nature_id

    @api.model
    def _get_cnae(self, raw_code):
        code = punctuation_rm(raw_code)
        cnae_id = False

        if code:
            cnae_id = (
                self.env["l10n_br_fiscal.cnae"]
                .search([("code_unmasked", "=", code)])
                .id
            )

        return cnae_id

    #
    # RECEITA WS
    #

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
            "legal_nature_id": self._receitaws_get_legal_nature(data),
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
    def _receitaws_get_legal_nature(self, data):
        legal_nature = data.get("natureza_juridica")
        if legal_nature:
            legal_nature = legal_nature.split(" - ")
            if len(legal_nature) > 1:
                legal_nature_code = legal_nature[0]
                return self._get_legal_nature(legal_nature_code)
        return False

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

    #
    # SERPRO
    #

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
        cep = self.get_data(address, "cep")

        res = {
            "legal_name": legal_name,
            "name": name,
            "email": self.get_data(data, "correioEletronico"),
            "street_name": self.get_data(address, "logradouro", title=True),
            "street2": self.get_data(address, "complemento", title=True),
            "district": self.get_data(address, "bairro", title=True),
            "street_number": self.get_data(address, "numero"),
            "legal_nature_id": self._serpro_get_legal_nature(data),
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
            "child_ids": [Command.set(child_ids)],
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
    def _serpro_get_legal_nature(self, data):
        legal_nature = data.get("naturezaJuridica")
        legal_nature_code = self.get_data(legal_nature, "codigo")
        return self._get_legal_nature(legal_nature_code)

    @api.model
    def _serpro_get_cnae(self, data):
        cnae_main = data.get("cnaePrincipal")
        cnae_code = self.get_data(cnae_main, "codigo")
        return self._get_cnae(cnae_code)
