# @ 2020 KMEE INFORMATICA LTDA - www.kmee.com.br -
#   Gabriel Cardoso de Faria <gabriel.cardoso@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from OpenSSL import crypto
from base64 import b64encode
from datetime import timedelta, datetime

from odoo import fields
from odoo.tools.misc import format_date
import base64
import os
import logging

from odoo.tests.common import TransactionCase
from odoo.addons import l10n_br_nfe

_logger = logging.getLogger(__name__)


class TestNFeExport(TransactionCase):
    def setUp(self):
        super(TestNFeExport, self).setUp()
        self.nfe = self.env.ref('l10n_br_nfe.demo_nfe_same_state')
        self.nfe.company_id.country_id.name = 'Brasil'
        self.nfe.action_document_back2draft()

        self.cert_country = "BR"
        self.cert_issuer_a = "EMISSOR A TESTE"
        self.cert_issuer_b = "EMISSOR B TESTE"
        self.cert_subject_valid = "CERTIFICADO VALIDO TESTE"
        self.cert_date_exp = fields.Datetime.today() + timedelta(days=365)
        self.cert_subject_invalid = "CERTIFICADO INVALIDO TESTE"
        self.cert_passwd = "123456"
        self.cert_name = "{} - {} - {} - Valid: {}".format(
            "NF-E",
            "A1",
            self.cert_subject_valid,
            format_date(self.env, self.cert_date_exp),
        )
        self.certificate_model = self.env["l10n_br_fiscal.certificate"]

        self.certificate_valid = self._create_certificate(
            valid=True, passwd=self.cert_passwd, issuer=self.cert_issuer_a,
            country=self.cert_country, subject=self.cert_subject_valid)

        cert = self.certificate_model.create(
            {
                'type': 'nf-e',
                'subtype': 'a1',
                'password': self.cert_passwd,
                'file': self.certificate_valid
            }
        )
        self.nfe.company_id.certificate_nfe_id = cert
        self.nfe.company_id.street_number = '3'

    def _create_certificate(self, valid=True, passwd=None, issuer=None,
                            country=None, subject=None):
        """Creating a fake certificate"""

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

    def test_serialize_xml(self):
        xml_path = os.path.join(
            l10n_br_nfe.__path__[0], 'tests', 'nfe', 'v4_00', 'leiauteNFe',
            'NFe35200697231608000169550010000000111855451724-nf-e.xml')
        with open(xml_path) as f:
            xml_string = f.read().replace('\n', '')
        self.nfe.nfe40_detPag = [(5, 0, 0), (0, 0, {
            'nfe40_indPag': '0',
            'nfe40_tPag': '99',
            'nfe40_vPag': self.nfe.amount_total,
        })]
        self.nfe.nfe40_detPag.__class__._field_prefix = 'nfe40_'
        self.nfe.action_document_confirm()
        self.nfe.date = datetime.strptime(
            '2020-06-04T11:58:46', '%Y-%m-%dT%H:%M:%S')
        self.nfe.date_in_out = datetime.strptime(
            '2020-06-04T11:58:46', '%Y-%m-%dT%H:%M:%S')
        self.nfe._document_export()
        nfe_xml = base64.b64decode(self.nfe.file_xml_id.datas).decode('utf-8')
        self.assertEqual(nfe_xml, xml_string, "Erro na serialização!")
