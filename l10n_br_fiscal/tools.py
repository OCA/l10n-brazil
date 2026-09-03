# Copyright (C) 2020  Renato Lima - Akretion <renato.lima@akretion.com.br>
# Copyright (C) 2014  KMEE - www.kmee.com.br
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import logging
import os
from unicodedata import normalize

from erpbrasil.base.misc import punctuation_rm

from odoo import SUPERUSER_ID, _, api, tools

from .constants.fiscal import EVENT_ENV_HML, EVENT_ENV_PROD

_logger = logging.getLogger(__name__)


def domain_field_codes(
    field_codes,
    field_name="code_unmasked",
    delimiter=",",
    operator1="=",
    operator2="=ilike",
    code_size=8,
):
    field_codes = field_codes.replace(" ", "").replace(".", "")
    if delimiter == ",":
        field_codes = field_codes.replace(";", ",")
    list_codes = [c for c in field_codes.split(delimiter) if c]

    domain = []

    if (
        len(list_codes) > 1
        and operator1 not in ("!=", "not ilike")
        and operator2 not in ("!=", "not ilike")
    ):
        domain += ["|"] * (len(list_codes) - 1)

    for n in list_codes:
        if "_" in n:
            code_part, exception_part = n.split("_", 1)
            domain += [
                "&",
                (field_name, operator1, code_part),
                ("exception", operator1, exception_part),
            ]
        elif len(n) == code_size:
            domain.append((field_name, operator1, n))
        elif len(n) < code_size:
            domain.append((field_name, operator2, n + "%"))

    return domain


def path_edoc_company(company_id):
    db_name = company_id._cr.dbname
    filestore = tools.config.filestore(db_name)
    return "/".join([filestore, "edoc", punctuation_rm(company_id.vat)])


def build_edoc_path(
    company_id, ambiente, tipo_documento, ano, mes, serie=False, numero=False
):
    caminho = path_edoc_company(company_id)

    if ambiente not in (EVENT_ENV_PROD, EVENT_ENV_HML):
        _logger.error("Ambiente não informado, salvando na pasta de Homologação!")

    if ambiente == EVENT_ENV_PROD:
        caminho = os.path.join(caminho, "producao/")
    else:
        caminho = os.path.join(caminho, "homologacao/")

    caminho = os.path.join(caminho, tipo_documento)
    caminho = os.path.join(caminho, str(ano) + "-" + str(mes) + "/")

    if serie and numero:
        caminho = os.path.join(caminho, str(serie) + "-" + str(numero) + "/")
    try:
        os.makedirs(caminho, exist_ok=True)
    except Exception as e:
        _logger.error(f"Falha de permissão ao acessar diretorio do e-doc {e}")
    return caminho


def remove_non_ascii_characters(value):
    result = ""
    if value and isinstance(value, str):
        result = (
            normalize("NFKD", value)
            .encode("ASCII", "ignore")
            .decode("ASCII")
            .replace("\n", "")
            .replace("\r", "")
            .strip()
        )

    return result


def set_journal_in_fiscal_operation(cr, company, values):
    """
    Set Journal in Fiscal Operation by 'ir.property'
    :param company: Company Object
    :param values: Dict with Journal and Fiscal Operation
    """
    _logger.info(
        f"Create or Inform Journal in Fiscal Operation for {company.name} Property ..."
    )
    env = api.Environment(cr, SUPERUSER_ID, {})
    for value in values:
        fiscal_operation = value.get("fiscal_operation")
        journal = value.get("journal")
        data_op_fiscal = "l10n_br_fiscal.operation," + str(env.ref(fiscal_operation).id)
        property_fiscal_op = env["ir.property"].search(
            [
                ("res_id", "=", data_op_fiscal),
                ("company_id", "=", company.id),
            ]
        )

        data_journal = "account.journal," + str(env.ref(journal).id)
        if property_fiscal_op:
            property_fiscal_op.value_reference = data_journal
        else:
            env["ir.property"].create(
                {
                    "name": f"{fiscal_operation}_{journal}",
                    "fields_id": env["ir.model.fields"]
                    .search(
                        [
                            ("model", "=", "l10n_br_fiscal.operation"),
                            ("name", "=", "journal_id"),
                        ]
                    )
                    .id,
                    "value": data_journal,
                    "res_id": data_op_fiscal,
                    "company_id": company.id,
                }
            )


def cfop_geography_warning(cfop_code, issuer_partner, company):
    """Warn when a declared CFOP scope contradicts the real geography.

    CFOP first digit: 1/5 = intrastate, 2/6 = interstate,
    3/7 = foreign trade. Returns a translated message or False.
    """
    if not cfop_code:
        return False
    declared = cfop_code[0]
    issuer_country = issuer_partner.country_id
    company_country = company.country_id
    if declared in ("3", "7"):
        if issuer_country and company_country and issuer_country == company_country:
            return _(
                "Declared CFOP %(cfop)s is a foreign trade CFOP but issuer "
                "and company are both in %(country)s."
            ) % {"cfop": cfop_code, "country": company_country.name}
        return False
    if issuer_country and company_country and issuer_country != company_country:
        return _(
            "Declared CFOP %(cfop)s is a domestic CFOP but issuer "
            "(%(issuer)s) and company (%(company)s) are in different "
            "countries."
        ) % {
            "cfop": cfop_code,
            "issuer": issuer_country.name,
            "company": company_country.name,
        }
    issuer_state = issuer_partner.state_id
    company_state = company.state_id
    if not issuer_state or not company_state:
        return False
    same_state = issuer_state == company_state
    if declared in ("1", "5") and not same_state:
        return _(
            "Declared CFOP %(cfop)s is intrastate but issuer (%(issuer)s) "
            "and company (%(company)s) are in different states."
        ) % {
            "cfop": cfop_code,
            "issuer": issuer_state.code,
            "company": company_state.code,
        }
    if declared in ("2", "6") and same_state:
        return _(
            "Declared CFOP %(cfop)s is interstate but issuer and company "
            "are both in %(state)s."
        ) % {"cfop": cfop_code, "state": company_state.code}
    return False
