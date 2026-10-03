# Copyright 2026 Akretion (Raphaël Valyi <raphael.valyi@akretion.com>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from unittest import mock

from erpbrasil.assinatura import misc
from xsdata.formats.dataclass.transports import DefaultTransport

from odoo.tests import TransactionCase

from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    DOCUMENT_STATE_CANCEL,
    SITUACAO_FISCAL_CANCELADO,
)
from odoo.addons.l10n_br_fiscal_edi.constants.fiscal import (
    DOCUMENT_STATE_AUTHORIZED,
    DOCUMENT_STATE_REJECTED,
)

from .test_mdfe_serialize import TestMDFeSerialize

# Same shape as the MDFeRecepcaoSinc synchronous response
# (retEnviMDFe embedding a protMDFe, see nfelib tests/mdfe/test_client.py).
RESPONSE_AUTORIZADA = b"""<?xml version="1.0" encoding="utf-8"?>
<soap12:Envelope
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xmlns:xsd="http://www.w3.org/2001/XMLSchema"
    xmlns:soap12="http://www.w3.org/2003/05/soap-envelope"
>
    <soap12:Body>
        <mdfeRecepcaoResult xmlns="http://www.portalfiscal.inf.br/mdfe/wsdl/MDFeRecepcaoSinc">
            <retEnviMDFe versao="3.00" xmlns="http://www.portalfiscal.inf.br/mdfe">
                <tpAmb>2</tpAmb>
                <cUF>41</cUF>
                <verAplic>MDFe_2.2.2</verAplic>
                <cStat>104</cStat>
                <xMotivo>Lote processado</xMotivo>
                <protMDFe versao="3.00">
                    <infProt>
                        <tpAmb>2</tpAmb>
                        <verAplic>MDFe_2.2.2</verAplic>
                        <chMDFe>41240200000000000100580010000000101000000104</chMDFe>
                        <dhRecbto>2024-02-15T15:01:00-03:00</dhRecbto>
                        <nProt>141000000000001</nProt>
                        <cStat>100</cStat>
                        <xMotivo>Autorizado o uso do MDF-e</xMotivo>
                    </infProt>
                </protMDFe>
            </retEnviMDFe>
        </mdfeRecepcaoResult>
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
        <mdfeRecepcaoResult xmlns="http://www.portalfiscal.inf.br/mdfe/wsdl/MDFeRecepcaoSinc">
            <retEnviMDFe versao="3.00" xmlns="http://www.portalfiscal.inf.br/mdfe">
                <tpAmb>2</tpAmb>
                <cUF>41</cUF>
                <verAplic>MDFe_2.2.2</verAplic>
                <cStat>215</cStat>
                <xMotivo>Rejeicao: Falha no schema XML</xMotivo>
            </retEnviMDFe>
        </mdfeRecepcaoResult>
    </soap12:Body>
</soap12:Envelope>
"""


RESPONSE_CANCELADA = b"""<?xml version="1.0" encoding="utf-8"?>
<soap12:Envelope
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xmlns:xsd="http://www.w3.org/2001/XMLSchema"
    xmlns:soap12="http://www.w3.org/2003/05/soap-envelope"
>
    <soap12:Body>
        <mdfeRecepcaoEventoResult xmlns="http://www.portalfiscal.inf.br/mdfe/wsdl/MDFeRecepcaoEvento">
            <retEventoMDFe versao="3.00" xmlns="http://www.portalfiscal.inf.br/mdfe">
                <infEvento>
                    <tpAmb>2</tpAmb>
                    <verAplic>MDFe_2.2.2</verAplic>
                    <cOrgao>41</cOrgao>
                    <cStat>135</cStat>
                    <xMotivo>Evento registrado e vinculado ao MDF-e</xMotivo>
                    <chMDFe>{chave}</chMDFe>
                    <tpEvento>110111</tpEvento>
                    <nSeqEvento>1</nSeqEvento>
                    <dhRegEvento>2024-02-15T15:10:00-03:00</dhRegEvento>
                    <nProt>141240000000002</nProt>
                </infEvento>
            </retEventoMDFe>
        </mdfeRecepcaoEventoResult>
    </soap12:Body>
</soap12:Envelope>
"""


class MDFeNfelibSoapTest(TestMDFeSerialize, TransactionCase):
    """MDF-e transmission through the nfelib client (mocked transport).

    Reuses TestMDFeSerialize.setUpClass to get a fully prepared demo MDF-e
    (confirmed, exported and signed) ready for transmission.
    """

    @classmethod
    def setUpClass(cls):
        mdfe_list = [
            {
                "record_ref": "l10n_br_mdfe.demo_mdfe_lc_modal_rodoviario",
                "xml_file": "MDFe35230905472475000102580200000602071611554500.xml",
            },
        ]
        super().setUpClass(mdfe_list)
        cls.mdfe = cls.mdfe_list[0]["mdfe"]

        cls.env["ir.config_parameter"].sudo().set_param(
            "l10n_br_mdfe.nfelib_soap_transmission", "True"
        )

    @classmethod
    def prepare_test_mdfe(cls, mdfe):
        # The company certificate must exist before the demo document is
        # confirmed: _check_mdfe_required_fields blocks a confirm without it.
        company = mdfe.company_id
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
        return super().prepare_test_mdfe(mdfe)

    def _send_with_response(self, response):
        with mock.patch.object(DefaultTransport, "post") as mock_post:
            mock_post.return_value = response
            self.mdfe._mdfe_send_for_authorization()

    def test_processor_is_nfelib_client(self):
        from nfelib.mdfe.client.v3_0.mdfe import MdfeClient

        processor = self.mdfe._nfelib_edoc_processor()
        self.assertIsInstance(processor, MdfeClient)

    def test_authorization(self):
        self._send_with_response(RESPONSE_AUTORIZADA)
        self.assertEqual(self.mdfe.state_edoc, DOCUMENT_STATE_AUTHORIZED)
        self.assertEqual(self.mdfe.status_code, "100")
        self.assertEqual(
            self.mdfe.authorization_event_id.protocol_number, "141000000000001"
        )

    def test_rejection(self):
        self._send_with_response(RESPONSE_REJEITADA)
        self.assertEqual(self.mdfe.state_edoc, DOCUMENT_STATE_REJECTED)
        self.assertEqual(self.mdfe.status_code, "215")

    def test_cancel(self):
        """Cancel an authorized MDF-e through the nfelib event service."""
        # authorize first so there is a protocol to cancel
        self._send_with_response(RESPONSE_AUTORIZADA)
        self.assertEqual(self.mdfe.state_edoc, DOCUMENT_STATE_AUTHORIZED)

        response = RESPONSE_CANCELADA.replace(
            b"{chave}", self.mdfe.document_key.encode()
        )
        with mock.patch.object(DefaultTransport, "post") as mock_post:
            mock_post.return_value = response
            self.mdfe.cancel_reason = "Cancelamento de teste com justificativa valida"
            self.mdfe._mdfe_cancel()

            # the signed event must be injected raw in the payload
            sent = mock_post.call_args.kwargs["data"]
            self.assertIn("Signature", sent)
            self.assertIn("110111", sent)  # tpEvento cancelamento

        self.assertEqual(self.mdfe.state_edoc, DOCUMENT_STATE_CANCEL)
        self.assertEqual(self.mdfe.state_fiscal, SITUACAO_FISCAL_CANCELADO)
        self.assertEqual(self.mdfe.cancel_event_id.protocol_number, "141240000000002")
