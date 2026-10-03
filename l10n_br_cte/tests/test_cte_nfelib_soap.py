# Copyright 2026 Akretion (Raphaël Valyi <raphael.valyi@akretion.com>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from unittest import mock

from erpbrasil.assinatura import misc
from xsdata.formats.dataclass.transports import DefaultTransport

from odoo.tests import TransactionCase

from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    SITUACAO_EDOC_AUTORIZADA,
    SITUACAO_EDOC_REJEITADA,
)

from .test_cte_serialize import TestCTeSerialize

# Same shape as the CTeRecepcaoSincV4 synchronous response
# (retCTe embedding a protCTe).
RESPONSE_AUTORIZADA = b"""<?xml version="1.0" encoding="utf-8"?>
<soap12:Envelope
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xmlns:xsd="http://www.w3.org/2001/XMLSchema"
    xmlns:soap12="http://www.w3.org/2003/05/soap-envelope"
>
    <soap12:Body>
        <cteRecepcaoResult xmlns="http://www.portalfiscal.inf.br/cte/wsdl/CTeRecepcaoSincV4">
            <retCTe versao="4.00" xmlns="http://www.portalfiscal.inf.br/cte">
                <tpAmb>2</tpAmb>
                <cUF>41</cUF>
                <verAplic>CTe_4.0</verAplic>
                <cStat>100</cStat>
                <xMotivo>Autorizado o uso do CT-e</xMotivo>
                <protCTe versao="4.00">
                    <infProt>
                        <tpAmb>2</tpAmb>
                        <verAplic>CTe_4.0</verAplic>
                        <chCTe>35240781583054000129570010000057311040645894</chCTe>
                        <dhRecbto>2024-07-11T09:05:32-03:00</dhRecbto>
                        <nProt>141240000000001</nProt>
                        <cStat>100</cStat>
                        <xMotivo>Autorizado o uso do CT-e</xMotivo>
                    </infProt>
                </protCTe>
            </retCTe>
        </cteRecepcaoResult>
    </soap12:Body>
</soap12:Envelope>
"""

RESPONSE_REJEITADA = b"""<?xml version="1.0" encoding="utf-8"?>
<soap12:Envelope
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xmlns:xsd="http://www.w3.org/2001/XMLSchema"
    xmlns:soap12="http://www.w3.org/2003/05/soap-envelope"
>
    <soap12:Body>
        <cteRecepcaoResult xmlns="http://www.portalfiscal.inf.br/cte/wsdl/CTeRecepcaoSincV4">
            <retCTe versao="4.00" xmlns="http://www.portalfiscal.inf.br/cte">
                <tpAmb>2</tpAmb>
                <cUF>41</cUF>
                <verAplic>CTe_4.0</verAplic>
                <cStat>214</cStat>
                <xMotivo>Rejeicao: Tamanho de arquivo excede o limite
                permitido</xMotivo>
            </retCTe>
        </cteRecepcaoResult>
    </soap12:Body>
</soap12:Envelope>
"""


class CTaNfelibSoapTest(TestCTeSerialize, TransactionCase):
    """CT-e transmission through the nfelib client (mocked transport).

    Reuses TestCTeSerialize.setUpClass to get a fully prepared demo CT-e
    (confirmed, exported) ready for transmission.
    """

    @classmethod
    def setUpClass(cls):
        cte_list = [
            {
                "record_ref": "l10n_br_cte.demo_cte_lc_modal_rodoviario",
                "xml_file": "CTe35240781583054000129570010000057311040645894.xml",
            },
        ]
        super().setUpClass(cte_list)
        cls.cte = cls.cte_list[0]["cte"]

        cls.env["ir.config_parameter"].sudo().set_param(
            "l10n_br_cte.nfelib_soap_transmission", "True"
        )
        company = cls.cte.company_id
        certificate_valid = misc.create_fake_certificate_file(
            valid=True,
            passwd="123456",
            issuer="EMISSOR A TESTE",
            country="BR",
            subject="CERTIFICADO VALIDO TESTE",
        )
        certificate_id = cls.env["l10n_br_fiscal.certificate"].create(
            {
                "type": "nf-e",
                "subtype": "a1",
                "password": "123456",
                "file": certificate_valid,
            }
        )
        company.certificate_nfe_id = certificate_id

    def _send_with_response(self, response):
        with mock.patch.object(DefaultTransport, "post") as mock_post:
            mock_post.return_value = response
            self.cte._cte_send_for_authorization()

    def test_processor_is_nfelib_client(self):
        from nfelib.cte.client.v4_0.cte import CteClient

        processor = self.cte._nfelib_edoc_processor()
        self.assertIsInstance(processor, CteClient)

    def test_authorization(self):
        self._send_with_response(RESPONSE_AUTORIZADA)
        self.assertEqual(self.cte.state_edoc, SITUACAO_EDOC_AUTORIZADA)
        self.assertEqual(self.cte.status_code, "100")
        self.assertEqual(
            self.cte.authorization_event_id.protocol_number, "141240000000001"
        )

    def test_rejection(self):
        self._send_with_response(RESPONSE_REJEITADA)
        self.assertEqual(self.cte.state_edoc, SITUACAO_EDOC_REJEITADA)
        self.assertEqual(self.cte.status_code, "214")
