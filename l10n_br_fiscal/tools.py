# Copyright (C) 2020  Renato Lima - Akretion <renato.lima@akretion.com.br>
# Copyright (C) 2014  KMEE - www.kmee.com.br
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import logging
import os
from unicodedata import normalize

from erpbrasil.base.misc import punctuation_rm

from odoo import SUPERUSER_ID, api, tools

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
    field_codes = field_codes.replace(".", "")
    list_codes = field_codes.split(delimiter)

    domain = []

    if (
        len(list_codes) > 1
        and operator1 not in ("!=", "not ilike")
        and operator2 not in ("!=", "not ilike")
    ):
        domain += ["|"] * (len(list_codes) - 1)

    for n in list_codes:
        if len(n) == code_size:
            domain.append((field_name, operator1, n))

        if len(n) < code_size:
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
    Set Journal in Fiscal Operation by updating the company-dependent journal_id field.
    :param company: Company Object
    :param values: Dict with Journal and Fiscal Operation
    """
    _logger.info(f"Create or Inform Journal in Fiscal Operation for {company.name} ...")
    env = api.Environment(cr, SUPERUSER_ID, {})
    for value in values:
        fiscal_operation = value.get("fiscal_operation")
        journal = value.get("journal")
        operation = env.ref(fiscal_operation)
        journal_record = env.ref(journal)
        # Set the journal_id for the specific company using company_dependent field
        operation.with_company(company).journal_id = journal_record
