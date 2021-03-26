# Copyright (C) 2020  Renato Lima - Akretion <renato.lima@akretion.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from base64 import b64encode

from OpenSSL import crypto

from ..constants.fiscal import (
    CERTIFICATE_TYPE_NFE
)


def domain_field_codes(field_codes, field_name="code_unmasked",
                       delimiter=",", operator1="=",
                       operator2="=ilike", code_size=8):
    field_codes = field_codes.replace('.', '')
    list_codes = field_codes.split(delimiter)

    domain = []

    if (len(list_codes) > 1
            and operator1 not in ('!=', 'not ilike')
            and operator2 not in ('!=', 'not ilike')):
        domain += ['|'] * (len(list_codes) - 1)

    for n in list_codes:
        if len(n) == code_size:
            domain.append((field_name, operator1, n))

        if len(n) < code_size:
            domain.append((field_name, operator2, n + '%'))

    return domain


def prepare_fake_certificate_vals(
        valid=True, passwd='123456', issuer="EMISSOR A TESTE",
        country='BR', subject="CERTIFICADO VALIDO TESTE",
        cert_type=CERTIFICATE_TYPE_NFE):
    return {
        'type': cert_type,
        'subtype': 'a1',
        'password': passwd,
        'file': create_fake_certificate_file(
            valid, passwd, issuer, country, subject
        ),
    }


def create_fake_certificate_file(valid, passwd, issuer, country, subject):
    """ Creating a fake certificate

        TODO: Move this method to erpbrasil

    :param valid: True or False
    :param passwd: Some password
    :param issuer: Some string, like EMISSOR A TESTE
    :param country: Some country: BR
    :param subject: Some string: CERTIFICADO VALIDO TESTE
    :return: base64 file
    """
    key = crypto.PKey()
    key.generate_key(crypto.TYPE_RSA, 2048)

    cert = crypto.X509()

    cert.get_issuer().C = country
    cert.get_issuer().CN = issuer

    cert.get_subject().C = country
    cert.get_subject().CN = subject

    cert.set_serial_number(2009)

    if valid:
        time_before = 0
        time_after = 365 * 24 * 60 * 60
    else:
        time_before = -1 * (365 * 24 * 60 * 60)
        time_after = 0

    cert.gmtime_adj_notBefore(time_before)
    cert.gmtime_adj_notAfter(time_after)
    cert.set_pubkey(key)
    cert.sign(key, 'md5')

    p12 = crypto.PKCS12()
    p12.set_privatekey(key)
    p12.set_certificate(cert)

    return b64encode(p12.export(passwd))
