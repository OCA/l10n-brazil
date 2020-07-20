# Copyright 2020 KMEE INFORMATICA LTDA
#   Gabriel Cardoso de Faria <gabriel.cardoso@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from base64 import b64encode
from xmldiff import main
import os
import logging
from OpenSSL import crypto

from odoo.tests.common import TransactionCase
from datetime import datetime, timedelta
from odoo.tools import config
from odoo import fields
from odoo.tools.misc import format_date
from ... import l10n_br_nfse_ginfes

_logger = logging.getLogger(__name__)


class TestFiscalDocumentNFSeGinfes(TransactionCase):

    def setUp(self):
        super(TestFiscalDocumentNFSeGinfes, self).setUp()

        self.nfse_same_state = self.env.ref(
            'l10n_br_nfse.demo_nfse_same_state'
        )
        self.company_ginfes = self.env.ref(
            'l10n_br_fiscal.empresa_simples_nacional')

        self.company_ginfes.processador_edoc = 'erpbrasil_edoc'
        self.company_ginfes.partner_id.inscr_mun = '35172'
        self.company_ginfes.partner_id.inscr_est = ''
        self.company_ginfes.partner_id.state_id = self.env.ref(
            'base.state_br_mg')
        self.company_ginfes.partner_id.city_id = self.env.ref(
            'l10n_br_base.city_3132404')
        self.company_ginfes.icms_regulation_id = self.env.ref(
            'l10n_br_fiscal.tax_icms_regulation').id
        self.company_ginfes.city_taxation_code_id = self.env.ref(
            'l10n_br_fiscal.city_taxation_code_itajuba').id
        self.company_ginfes.document_type_id = self.env.ref(
            'l10n_br_fiscal.document_SE')

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

        self.company_ginfes.certificate_nfe_id = cert
        self.nfse_same_state.company_id = self.company_ginfes.id

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

    def test_nfse_ginfes(self):
        """ Test NFS-e same state. """

        self.nfse_same_state._onchange_document_serie_id()
        self.nfse_same_state._onchange_partner_id()
        self.nfse_same_state._onchange_fiscal_operation_id()
        self.nfse_same_state._onchange_company_id()
        self.nfse_same_state.rps_number = 50
        self.nfse_same_state.date = datetime.strptime(
            '2020-06-04T11:58:46', '%Y-%m-%dT%H:%M:%S')

        for line in self.nfse_same_state.line_ids:
            line._onchange_product_id_fiscal()
            line._onchange_commercial_quantity()
            line._onchange_ncm_id()
            line._onchange_fiscal_operation_id()
            line._onchange_fiscal_operation_line_id()
            line._onchange_fiscal_taxes()

        self.nfse_same_state.action_document_confirm()

        xml_path = os.path.join(
            l10n_br_nfse_ginfes.__path__[0], 'tests', 'nfse',
            '001_50_nfse.xml')
        output = os.path.join(config['data_dir'], 'filestore', self.cr.dbname,
                              self.nfse_same_state.file_xml_id.store_fname)
        _logger.info("XML file saved at %s" % (output,))

        diff = main.diff_files(xml_path, output)
        _logger.info("Diff with expected XML (if any): %s" % (diff,))
        assert len(diff) == 0
