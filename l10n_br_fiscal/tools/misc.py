# Copyright (C) 2020  Renato Lima - Akretion <renato.lima@akretion.com.br>
# Copyright (C) 2014  KMEE - www.kmee.com.br
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import datetime
import logging
import os
from base64 import b64encode

from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import BestAvailableEncryption
from cryptography.hazmat.primitives.serialization.pkcs12 import (
    serialize_key_and_certificates,
)
from cryptography.x509.oid import NameOID
from erpbrasil.base.misc import punctuation_rm

from odoo.tools import config

from ..constants.fiscal import CERTIFICATE_TYPE_NFE, EVENT_ENV_HML, EVENT_ENV_PROD

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


def prepare_fake_certificate_vals(
    valid=True,
    passwd="123456",
    issuer="EMISSOR A TESTE",
    country="BR",
    subject="CERTIFICADO VALIDO TESTE",
    cert_type=CERTIFICATE_TYPE_NFE,
):
    return {
        "type": cert_type,
        "subtype": "a1",
        "password": passwd,
        "file": create_fake_certificate_file(valid, passwd, issuer, country, subject),
    }


def create_fake_certificate_file(valid, passwd, issuer, country, subject):
    """Creating a fake certificate

        TODO: Move this method to erpbrasil

    :param valid: True or False
    :param passwd: Some password
    :param issuer: Some string, like EMISSOR A TESTE
    :param country: Some country: BR
    :param subject: Some string: CERTIFICADO VALIDO TESTE
    :return: base64 file
    """
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )

    public_key = private_key.public_key()
    builder = x509.CertificateBuilder()

    builder = builder.subject_name(
        x509.Name(
            [
                x509.NameAttribute(NameOID.COMMON_NAME, subject),
                x509.NameAttribute(NameOID.COUNTRY_NAME, country),
            ]
        )
    )

    builder = builder.issuer_name(
        x509.Name(
            [
                x509.NameAttribute(NameOID.COMMON_NAME, issuer),
                x509.NameAttribute(NameOID.COUNTRY_NAME, country),
            ]
        )
    )

    one_year = datetime.timedelta(365, 0, 0)
    today = datetime.datetime.today()

    if valid:
        time_before = today
        time_after = today + one_year
    else:
        time_before = today - one_year
        time_after = today

    builder = builder.not_valid_before(time_before)
    builder = builder.not_valid_after(time_after)

    builder = builder.serial_number(2009)

    builder = builder.public_key(public_key)

    certificate = builder.sign(
        private_key=private_key,
        algorithm=hashes.MD5(),
    )

    p12 = serialize_key_and_certificates(
        name=subject.encode(),
        key=private_key,
        cert=certificate,
        cas=None,
        encryption_algorithm=BestAvailableEncryption(passwd.encode()),
    )

    return b64encode(p12)


def path_edoc_company(company_id):
    db_name = company_id._cr.dbname
    filestore = config.filestore(db_name)
    return "/".join([filestore, "edoc", punctuation_rm(company_id.cnpj_cpf)])


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
        _logger.error("Falha de permissão ao acessar diretorio do e-doc {}".format(e))
    return caminho
