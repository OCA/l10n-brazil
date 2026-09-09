# Copyright 2022 KMEE - Luis Felipe Mileo
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import csv
import logging
from datetime import datetime
from os.path import dirname

from erpbrasil.base.misc import punctuation_rm

from odoo import Command, api, models
from odoo.exceptions import UserError, ValidationError

from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    TAX_FRAMEWORK_NORMAL,
    TAX_FRAMEWORK_SIMPLES,
)

_logger = logging.getLogger(__name__)

RECEITAWS_URL = "https://www.receitaws.com.br/v1/cnpj/"

SERPRO_URL = "https://gateway.apiserpro.serpro.gov.br"
QUALIFICACAO_CSV = dirname(__file__) + "/../data/serpro_qualificacao.csv"

CPFCNPJ_URL = "https://api.cpfcnpj.com.br"
CPFCNPJ_DEFAULT_PACKAGE = "6"
# The Simples Nacional - Microempreendedor Individual (MEI) code from
# l10n_br_fiscal has no named constant, so it is declared here.
TAX_FRAMEWORK_MEI = "4"


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
        if hasattr(self, f"{self.get_provider()}_get_api_url"):
            return getattr(self, f"{self.get_provider()}_get_api_url")(cnpj)
        return False

    @api.model
    def get_headers(self):
        """Get webservice request headers"""
        if hasattr(self, f"{self.get_provider()}_get_headers"):
            return getattr(self, f"{self.get_provider()}_get_headers")()
        return False

    @api.model
    def validate(self, response):
        """Validate webservice response.

        Returns: data (dict)
        """
        if hasattr(self, f"{self.get_provider()}_validate"):
            return getattr(self, f"{self.get_provider()}_validate")(response)
        return False

    @api.model
    def import_data(self, data):
        """Import webservice response to Odoo

        Params:
            data (dict): data with webservice response

        Returns:
            values (dict): dict with res_partner fields and it's values
        """
        if hasattr(self, f"_{self.get_provider()}_import_data"):
            return getattr(self, f"_{self.get_provider()}_import_data")(data)
        return False

    @api.model
    def get_data(self, data, name, title=False, lower=False):
        value = False
        name_str = data.get(name)
        if name_str:
            value = name_str
            if isinstance(value, str):
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
            raise ValidationError(self.env._("%(reason)s", reason=response.reason))

    @api.model
    def _get_legal_nature(self, raw_code):
        code = punctuation_rm(raw_code)
        legal_nature_id = False
        if code:
            legal_nature_id = (
                self.env["l10n_br_fiscal.legal.nature"]
                .search([("code_unmasked", "=", code)], limit=1)
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
            raise ValidationError(self.env._(data.get("message")))

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

        return [Command.set(cnae_secondary)]

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
                if partner_cpf:
                    partner_cpf = "".join(
                        char for char in str(partner_cpf) if char.isalnum()
                    )
                values.update({"vat": partner_cpf})

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
            _logger.warning(str(error))
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

    #
    # CPFCNPJ (cpfcnpj.com.br)
    #

    @api.model
    def cpfcnpj_get_api_url(self, cnpj, package=None):
        """Build the provider endpoint.

        The optional package argument overrides the configured package, which is
        used to reach the state registration package (16) without changing the
        configured default. When omitted, the configured package is used.
        """
        token = self._get_cnpj_param("cpfcnpj_token")
        if not package:
            package = self._get_cnpj_param("cpfcnpj_package") or CPFCNPJ_DEFAULT_PACKAGE
        return f"{CPFCNPJ_URL}/{token}/{package}/{cnpj}"

    @api.model
    def cpfcnpj_get_headers(self):
        return {"Accept": "application/json"}

    @api.model
    def cpfcnpj_validate(self, response):
        self._validate(response)
        data = response.json()
        if not data.get("status"):
            raise ValidationError(
                self.env._("%(reason)s", reason=data.get("erro") or "")
            )
        return data

    @api.model
    def _cpfcnpj_import_data(self, data):
        legal_name = self.get_data(data, "razao", title=True)
        fantasy_name = self.get_data(data, "fantasia", title=True)
        address = data.get("matrizEndereco") or {}
        phone, mobile = self._cpfcnpj_get_phones(data)
        state_id, city_id = self._cpfcnpj_get_state_city(data, address)

        res = {
            "legal_name": legal_name,
            "name": fantasy_name if fantasy_name else legal_name,
            "email": self.get_data(data, "email", lower=True),
            "street_name": self.get_data(address, "logradouro", title=True),
            "street2": self.get_data(address, "complemento", title=True),
            "district": self.get_data(address, "bairro", title=True),
            "street_number": self.get_data(address, "numero"),
            "zip": self.get_data(address, "cep"),
            "legal_nature_id": self._cpfcnpj_get_legal_nature(data),
            "phone": phone,
            "mobile": mobile,
            "state_id": state_id,
            "city_id": city_id,
            "equity_capital": self.get_data(data, "capitalSocial"),
            "cnae_main_id": self._cpfcnpj_get_cnae(data),
            "cnae_secondary_ids": self._cpfcnpj_get_secondary_cnae(data),
        }

        tax_framework = self._cpfcnpj_get_tax_framework(data)
        if tax_framework:
            res["tax_framework"] = tax_framework

        res.update(self._cpfcnpj_get_registry_fields(data))
        res.update(self._cpfcnpj_import_partners(data))
        res.update(self._cpfcnpj_get_card_pdf(data))

        return res

    @api.model
    def _cpfcnpj_parse_date(self, value):
        """Parse a provider date string into a date object.

        The provider returns dates either as "YYYY-MM-DD" or as "DD/MM/YYYY".
        Anything that does not match one of these formats returns False.
        """
        if not value or not isinstance(value, str):
            return False
        value = value.strip()
        for date_format in ("%Y-%m-%d", "%d/%m/%Y"):
            try:
                return datetime.strptime(value, date_format).date()
            except ValueError:
                continue
        return False

    @api.model
    def _cpfcnpj_get_bool_param(self, param_name, default=False):
        """Read a boolean config parameter tolerating the several ways it may be
        stored ("True"/"False", "1"/"0") and falling back to the given default
        when the parameter is unset or empty.
        """
        raw = self._get_cnpj_param(param_name)
        if raw is False or raw is None or str(raw).strip() == "":
            return default
        return str(raw).strip().lower() not in ("0", "false", "no", "off", "f")

    @api.model
    def _cpfcnpj_get_status_reason(self, situacao):
        """Normalize the registration status reason.

        The provider may return the reason as a plain string, as a list (empty
        for active companies, one item otherwise) or as an object carrying a
        "descricao" key. All three shapes are handled here.
        """
        motivo = situacao.get("motivo")
        if not motivo:
            return False
        if isinstance(motivo, str):
            return motivo
        if isinstance(motivo, list):
            for item in motivo:
                if isinstance(item, str) and item:
                    return item
                if isinstance(item, dict):
                    reason = self.get_data(item, "descricao")
                    if reason:
                        return reason
            return False
        if isinstance(motivo, dict):
            return self.get_data(motivo, "descricao")
        return False

    @api.model
    def _cpfcnpj_get_branch_type(self, data):
        """Map the head office / branch indicator to the Odoo selection value.

        The information comes from "matrizfilial.tipo" or, as a fallback, from
        the top level "tipo" key. Both carry "Matriz" or "Filial".
        """
        matrizfilial = data.get("matrizfilial") or {}
        tipo = matrizfilial.get("tipo") or data.get("tipo")
        if not tipo:
            return False
        normalized = str(tipo).strip().lower()
        if normalized.startswith("matriz"):
            return "head_office"
        if normalized.startswith("filial"):
            return "branch"
        return False

    @api.model
    def _cpfcnpj_get_registry_fields(self, data):
        """Map the registry cadastral fields returned by package 6.

        Every value is optional and tolerant of missing keys.
        """
        situacao = data.get("situacao") or {}
        simples = data.get("simplesNacional") or {}
        responsavel_qualificacao = data.get("responsavelQualificacao") or {}

        return {
            "company_size": self.get_data(data.get("porte") or {}, "descricao"),
            "cnpj_status": self.get_data(situacao, "nome"),
            "cnpj_status_date": self._cpfcnpj_parse_date(situacao.get("data")),
            "cnpj_status_reason": self._cpfcnpj_get_status_reason(situacao),
            "opening_date": self._cpfcnpj_parse_date(data.get("inicioAtividade")),
            "cnpj_branch_type": self._cpfcnpj_get_branch_type(data),
            "simples_option_date": self._cpfcnpj_parse_date(simples.get("inicio")),
            "legal_responsible_name": self.get_data(data, "responsavel", title=True),
            "legal_responsible_function": self.get_data(
                responsavel_qualificacao, "descricao"
            ),
        }

    @api.model
    def _cpfcnpj_import_partners(self, data):
        """Materialize the QSA (company partners) as child res.partner records.

        This mirrors the SERPRO behaviour (see _import_additional_info): the
        partners are created inside import_data and linked to the target partner
        later, in the wizard, through child_ids. As in the SERPRO case, the
        parent is unknown at this point, so no de-duplication against existing
        children is attempted here.
        """
        if self._cpfcnpj_get_bool_param("cpfcnpj_skip_partners"):
            return {}

        socios = data.get("socios")
        if not isinstance(socios, list) or not socios:
            return {}

        child_ids = []
        for socio in socios:
            if not isinstance(socio, dict):
                continue
            name = self.get_data(socio, "nome", title=True)
            if not name:
                continue

            values = {"name": name}

            function = self.get_data(socio.get("qualificacao_socio") or {}, "descricao")
            if function:
                values["function"] = function

            doc = socio.get("cpf_cnpj_socio")
            doc_digits = (
                "".join(char for char in str(doc) if char.isalnum()) if doc else ""
            )
            tipo = str(socio.get("tipo") or "").strip().lower()
            is_person = "fisica" in tipo or len(doc_digits) == 11
            values["company_type"] = "person" if is_person else "company"

            # Only a full CPF (11) or CNPJ (14) becomes a vat. The 8 digit CNPJ
            # root of a company partner is not a valid vat and is skipped.
            if len(doc_digits) in (11, 14):
                values["vat"] = doc_digits

            comment = self._cpfcnpj_partner_comment(socio)
            if comment:
                values["comment"] = comment

            existing = self._cpfcnpj_find_existing_partner(values.get("vat"), name)
            if existing is None:
                # The document belongs to a contact of another company: leave
                # it alone instead of moving it under this partner.
                continue
            if existing:
                update = {
                    key: values[key] for key in ("function", "comment") if key in values
                }
                existing.write(update)
                child_ids.append(existing.id)
            else:
                child_ids.append(self.env["res.partner"].create(values).id)

        if not child_ids:
            return {}

        return {"child_ids": [Command.set(child_ids)]}

    @api.model
    def _cpfcnpj_find_existing_partner(self, vat, name):
        """Find the partner to reuse for a QSA entry so that running the
        wizard again does not create duplicates (l10n_br_base enforces a
        unique CPF/CNPJ per partner).

        A partner with the same vat is reused wherever it is; when it already
        belongs to another company, None is returned so the entry is skipped.
        Without a vat, only a child of the partner being updated (taken from
        the wizard context) with the same name is reused. Returns an empty
        recordset when nothing matches.
        """
        partner_model = self.env["res.partner"]
        parent_id = self.env.context.get("default_partner_id")
        if vat:
            existing = partner_model.search([("vat", "=", vat)], limit=1)
            if existing and existing.parent_id and existing.parent_id.id != parent_id:
                return None
            return existing
        if parent_id:
            return partner_model.search(
                [
                    ("parent_id", "=", parent_id),
                    ("name", "=", name),
                    ("vat", "=", False),
                ],
                limit=1,
            )
        return partner_model

    @api.model
    def _cpfcnpj_partner_comment(self, socio):
        """Build an optional note with the entry date and the legal
        representative (name and qualification) when they are present.
        """
        parts = []
        entry_date = self.get_data(socio, "data_entrada")
        if entry_date:
            parts.append(self.env._("Entry date: %(date)s", date=entry_date))

        representative = self.get_data(socio, "nome_representante", title=True)
        if representative:
            qualification = self.get_data(socio, "qualificacao_representante")
            if qualification:
                parts.append(
                    self.env._(
                        "Legal representative: %(name)s (%(function)s)",
                        name=representative,
                        function=qualification,
                    )
                )
            else:
                parts.append(
                    self.env._("Legal representative: %(name)s", name=representative)
                )

        return "\n".join(parts) if parts else False

    @api.model
    def _cpfcnpj_get_card_pdf(self, data):
        """Return the base64 CNPJ card PDF when enabled and present.

        The value is later turned into an ir.attachment by the wizard, so it is
        deliberately kept out of the res.partner write values.
        """
        if self._cpfcnpj_get_bool_param("cpfcnpj_skip_card"):
            return {}
        pdf = data.get("comprovantePdfBase64")
        if not pdf:
            return {}
        return {"cnpj_card_pdf": pdf}

    @api.model
    def _cpfcnpj_select_ie(self, data, uf):
        """Pick the state registration (package 16) to use.

        The active registration whose state matches the establishment UF is
        preferred; otherwise the first active one is used. Returns only the
        digits of the registration, or False when there is no active one.
        """
        if not isinstance(data, dict):
            return False
        registrations = data.get("inscricoesEstaduais") or []
        active = [
            reg for reg in registrations if isinstance(reg, dict) and reg.get("ativo")
        ]
        if not active:
            return False

        chosen = False
        if uf:
            for reg in active:
                estado = reg.get("estado") or {}
                if str(estado.get("sigla") or "").upper() == str(uf).upper():
                    chosen = reg
                    break
        if not chosen:
            chosen = active[0]

        ie_code = chosen.get("inscricao_estadual")
        if not ie_code:
            return False
        return "".join(char for char in str(ie_code) if char.isdigit()) or False

    @api.model
    def _cpfcnpj_format_phone(self, item):
        """Format a phone item as "(ddd) numero".

        Returns False when ddd or numero is missing, so an incomplete item is
        never rendered as "(None) None".
        """
        if not isinstance(item, dict):
            return False
        ddd = item.get("ddd")
        numero = item.get("numero")
        if not ddd or not numero:
            return False
        return f"({ddd}) {numero}"

    @api.model
    def _cpfcnpj_get_phones(self, data):
        """Return the first two complete phone numbers found in the response.

        Items missing ddd or numero are skipped. The first valid number is
        assigned to phone and the second, if any, to mobile. The remaining
        numbers are ignored.
        """
        phones = []
        for item in data.get("telefones") or []:
            formatted = self._cpfcnpj_format_phone(item)
            if formatted:
                phones.append(formatted)
            if len(phones) == 2:
                break
        phone = phones[0] if phones else False
        mobile = phones[1] if len(phones) > 1 else False
        return phone, mobile

    @api.model
    def _cpfcnpj_get_state_city(self, data, address):
        """Resolve state and city.

        The city is matched by its IBGE code (the most reliable key) and falls
        back to a case-insensitive name match within the state.
        """
        state_id = False
        city_id = False

        uf = self.get_data(address, "uf")
        if uf:
            state = self.env["res.country.state"].search(
                [("code", "=", uf), ("country_id.code", "=", "BR")],
                limit=1,
            )
            state_id = state.id

        ibge = data.get("ibge") or {}
        ibge_city = ibge.get("cidade") or {}
        ibge_code = ibge_city.get("ibge_id")
        if ibge_code:
            city = self.env["res.city"].search(
                [("ibge_code", "=", str(ibge_code))], limit=1
            )
            city_id = city.id
        elif state_id:
            city_name = self.get_data(address, "cidade", title=True)
            if city_name:
                city = self.env["res.city"].search(
                    [
                        ("name", "=ilike", city_name),
                        ("state_id", "=", state_id),
                    ],
                    limit=1,
                )
                city_id = city.id

        return [state_id, city_id]

    @api.model
    def _cpfcnpj_get_legal_nature(self, data):
        legal_nature = data.get("naturezaJuridica") or {}
        return self._get_legal_nature(self.get_data(legal_nature, "codigo"))

    @api.model
    def _cpfcnpj_get_cnae(self, data):
        cnae = data.get("cnae") or {}
        return self._get_cnae(self.get_data(cnae, "fiscal"))

    @api.model
    def _cpfcnpj_get_secondary_cnae(self, data):
        """Resolve the secondary CNAEs.

        The API returns the secondary CNAE id as a number, so it is converted
        to a string before being normalized.
        """
        cnae = data.get("cnae") or {}
        secondary = []
        for item in cnae.get("secundarias") or []:
            if not isinstance(item, dict):
                continue
            code = item.get("id")
            if code is None or code == "":
                continue
            cnae_id = self._get_cnae(str(code))
            if cnae_id:
                secondary.append(cnae_id)
        return [Command.set(secondary)]

    @api.model
    def _cpfcnpj_get_tax_framework(self, data):
        """Derive the Odoo fiscal tax framework from the Simples Nacional and
        SIMEI information returned by the provider.

        No other CNPJ provider fills res.partner.tax_framework today, so this
        mapping is the main fiscal value added by this backend. The rules are:

            SIMEI optante                -> Microempreendedor Individual (MEI)
            Simples Nacional optante     -> Simples Nacional
            otherwise                    -> Regime Normal

        Package 5 does not carry tax regime data, so the field is left untouched
        in that case.
        """
        simples = data.get("simplesNacional")
        simei = data.get("simei")
        if simples is None and simei is None:
            return False
        if self._cpfcnpj_is_optante(simei or {}):
            return TAX_FRAMEWORK_MEI
        if self._cpfcnpj_is_optante(simples or {}):
            return TAX_FRAMEWORK_SIMPLES
        return TAX_FRAMEWORK_NORMAL

    @api.model
    def _cpfcnpj_is_optante(self, info):
        return str(info.get("optante", "")).strip().lower() in ("sim", "true", "1")
