# Copyright 2020 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from base64 import b64encode
from datetime import timedelta
from OpenSSL import crypto

from odoo.tests.common import TransactionCase
from odoo.tools.misc import format_date
from odoo import fields


class TestFiscalDocumentNFSeCommon(TransactionCase):

        def setUp(self):
            super(TestFiscalDocumentNFSeCommon, self).setUp()

            self.nfse_same_state = self.env.ref(
                'l10n_br_fiscal.demo_nfse_same_state'
            )
            self.company = self.env.ref(
                'l10n_br_base.empresa_simples_nacional')

            self.company.processador_edoc = 'erpbrasil_edoc'
            self.company.partner_id.inscr_mun = '35172'
            self.company.partner_id.inscr_est = ''
            self.company.partner_id.state_id = self.env.ref(
                'base.state_br_mg')
            self.company.partner_id.city_id = self.env.ref(
                'l10n_br_base.city_3132404')
            self.company.icms_regulation_id = self.env.ref(
                'l10n_br_fiscal.tax_icms_regulation').id
            self.company.city_taxation_code_id = self.env.ref(
                'l10n_br_fiscal.city_taxation_code_itajuba').id
            self.company.document_type_id = self.env.ref(
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

            self.company.certificate_nfe_id = cert
            self.nfse_same_state.company_id = self.company.id

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

        def test_certified_nfse_same_state_(self):
            """ Test Certified NFSe same state. """

            self.nfse_same_state._onchange_document_serie_id()
            self.nfse_same_state._onchange_fiscal_operation_id()

            # RPS Number
            self.assertEquals(
                self.nfse_same_state.rps_number, '50',
                "Error to mappping RPS Number 50"
                " for Venda de Serviço de Contribuinte Dentro do Estado.")

            # RPS Type
            self.assertEquals(
                self.nfse_same_state.rps_type, '1',
                "Error to mappping RPS Type 1"
                " for Venda de Serviço de Contribuinte Dentro do Estado.")

            # Operation Nature
            self.assertEquals(
                self.nfse_same_state.operation_nature, '1',
                "Error to mappping Operation Nature 1"
                " for Venda de Serviço de Contribuinte Dentro do Estado.")

            # Taxation Special Regime
            self.assertEquals(
                self.nfse_same_state.taxation_special_regime, '1',
                "Error to mappping Taxation Special Regime 1"
                " for Venda de Serviço de Contribuinte Dentro do Estado.")

            for line in self.nfse_same_state.line_ids:
                line._onchange_product_id_fiscal()
                line._onchange_commercial_quantity()
                line._onchange_ncm_id()
                line._onchange_fiscal_operation_id()
                line._onchange_fiscal_operation_line_id()
                line._onchange_fiscal_taxes()

                # Fiscal Deductions Value
                self.assertEquals(
                    line.fiscal_deductions_value, 0.0,
                    "Error to mappping Fiscal Deductions Value 0.0"
                    " for Venda de Serviço de Contribuinte Dentro do Estado.")

                # City Taxation Code
                self.assertEquals(
                    line.city_taxation_code_id.code, '6311900',
                    "Error to mappping City Taxation Code 6311900"
                    " for Venda de Serviço de Contribuinte Dentro do Estado.")
