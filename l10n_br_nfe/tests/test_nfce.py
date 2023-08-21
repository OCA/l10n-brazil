# Copyright 2023 KMEE (Felipe Zago Rodrigues <felipe.zago@kmee.com.br>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
# pylint: disable=line-too-long

from datetime import datetime
from unittest import mock

from erpbrasil.assinatura import misc
from erpbrasil.edoc.resposta import analisar_retorno_raw
from nfelib.nfe.ws.edoc_legacy import DocumentoElectronicoAdapter as DocumentoEletronico
from nfelib.v4_00 import retEnvEvento, retEnviNFe, retInutNFe

from odoo.fields import Datetime

from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    AUTORIZADO,
    SITUACAO_EDOC_A_ENVIAR,
    SITUACAO_EDOC_AUTORIZADA,
    SITUACAO_EDOC_CANCELADA,
    SITUACAO_EDOC_DENEGADA,
    SITUACAO_EDOC_INUTILIZADA,
    SITUACAO_EDOC_REJEITADA,
)

from .test_nfe_serialize import TestNFeExport

# flake8: noqa: B950
response_autorizada = """<?xml version="1.0" encoding="utf-8"?><soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema"><soap:Body><nfeResultMsg xmlns="http://www.portalfiscal.inf.br/nfe/wsdl/NFeAutorizacao4"><retEnviNFe versao="4.00" xmlns="http://www.portalfiscal.inf.br/nfe"><tpAmb>2</tpAmb><verAplic>SVRSnfce202307311112</verAplic><cStat>104</cStat><xMotivo>Lote processado</xMotivo><cUF>33</cUF><dhRecbto>2023-08-07T11:09:08-03:00</dhRecbto><protNFe versao="4.00"><infProt><tpAmb>2</tpAmb><verAplic>SVRSnfce202307311112</verAplic><chNFe>33230807984267003800650040000000321935136447</chNFe><dhRecbto>2023-08-07T11:09:08-03:00</dhRecbto><nProt>333230000396082</nProt><digVal>zwJzbq4FXks09tlHU1GEWRI7t/A=</digVal><cStat>100</cStat><xMotivo>Autorizado o uso da NF-e</xMotivo></infProt></protNFe></retEnviNFe></nfeResultMsg></soap:Body></soap:Envelope>"""

response_denegada = """<?xml version="1.0" encoding="utf-8"?><soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema"><soap:Body><nfeResultMsg xmlns="http://www.portalfiscal.inf.br/nfe/wsdl/NFeAutorizacao4"><retEnviNFe xmlns="http://www.portalfiscal.inf.br/nfe" versao="4.00"><tpAmb>2</tpAmb><verAplic>1.0</verAplic><cStat>110</cStat><xMotivo>Uso Denegado: Irregularidade Fiscal do Emitente</xMotivo><cUF>33</cUF><dhRecbto>2023-08-07T12:40:00-03:00</dhRecbto><infRec><nRec>123456789012345</nRec><tMed>1</tMed></infRec></retEnviNFe></nfeResultMsg></soap:Body></soap:Envelope>"""

response_rejeitada = """<?xml version="1.0" encoding="utf-8"?><soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema"><soap:Body><nfeResultMsg xmlns="http://www.portalfiscal.inf.br/nfe/wsdl/NFeAutorizacao4"><retEnviNFe versao="4.00" xmlns="http://www.portalfiscal.inf.br/nfe"><tpAmb>2</tpAmb><verAplic>SVRSnfce202307311112</verAplic><cStat>225</cStat><xMotivo>Rejeicao: Falha no Schema XML da NFe</xMotivo><cUF>33</cUF><dhRecbto>2023-08-04T15:00:00-03:00</dhRecbto></retEnviNFe></nfeResultMsg></soap:Body></soap:Envelope>"""

response_inutilizacao = """<?xml version="1.0" encoding="utf-8"?><soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema"><soap:Body><nfeResultMsg xmlns="http://www.portalfiscal.inf.br/nfe/wsdl/NFeInutilizacao4"><retInutNFe versao="4.00" xmlns="http://www.portalfiscal.inf.br/nfe"><infInut><tpAmb>2</tpAmb><verAplic>SVRSnfce202307171617</verAplic><cStat>102</cStat><xMotivo>Inutilizacao de numero homologado</xMotivo><cUF>33</cUF><ano>23</ano><CNPJ>07984267003800</CNPJ><mod>65</mod><serie>4</serie><nNFIni>35</nNFIni><nNFFin>35</nNFFin><dhRecbto>2023-08-07T11:23:22-03:00</dhRecbto><nProt>333230000396102</nProt></infInut></retInutNFe></nfeResultMsg></soap:Body></soap:Envelope>"""

response_cancelamento = """<?xml version="1.0" encoding="UTF-8"?><soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"><soap:Body><nfeResultMsg xmlns="http://www.portalfiscal.inf.br/nfe/wsdl/NFeRecepcaoEvento4"><retEnvEvento xmlns="http://www.portalfiscal.inf.br/nfe" versao="1.00"><idLote /><tpAmb>2</tpAmb><verAplic>SVRS202305251555</verAplic><cStat>101</cStat><retEvento versao="1.00"><infEvento><tpAmb>2</tpAmb><verAplic>SVRS202305251555</verAplic><cStat>101</cStat><xMotivo>Era apenas um teste.</xMotivo><chNFe>33230807984267003800650040000000321935136447</chNFe><tpEvento>110111</tpEvento><xEvento>Cancelamento registrado</xEvento><nSeqEvento>1</nSeqEvento><CNPJDest>07984267003800</CNPJDest><dhRegEvento>2023-07-05T16:52:52-03:00</dhRegEvento><nProt>333230000396082</nProt></infEvento></retEvento></retEnvEvento></nfeResultMsg></soap:Body></soap:Envelope>"""

response_contingency = """<?xml version="1.0" encoding="UTF-8"?><soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema"><soap:Body><nfeResultMsg xmlns="http://www.portalfiscal.inf.br/nfe/wsdl/NFeAutorizacao4"><retEnviNFe xmlns="http://www.portalfiscal.inf.br/nfe" versao="4.00"><tpAmb>2</tpAmb><verAplic>4.0.0</verAplic><cStat>108</cStat><xMotivo>Rejeição: Duplicidade de NF-e</xMotivo><cUF>33</cUF><dhRecbto>2023-08-08T10:30:00-03:00</dhRecbto><infRec><nRec>123456789012345</nRec><tMed>1</tMed></infRec></retEnviNFe></nfeResultMsg></soap:Body></soap:Envelope>"""


class FakeRetorno(object):
    def __init__(self, text):
        self.text = text
        self.content = text.encode("utf-8")

    def raise_for_status(self):
        pass


def mocked_nfce_autorizada(*args, **kwargs):
    result = analisar_retorno_raw(
        "nfeAutorizacaoLote",
        object(),
        b"<fake_post/>",
        FakeRetorno(response_autorizada),
        retEnviNFe,
    )
    result.processo_xml = b"dummy"
    return result


def mocked_nfce_denegada(*args, **kwargs):
    result = analisar_retorno_raw(
        "nfeAutorizacaoLote",
        object(),
        b"<fake_post/>",
        FakeRetorno(response_denegada),
        retEnviNFe,
    )
    result.processo_xml = b"dummy"
    return result


def mocked_nfce_rejeitada(*args, **kwargs):
    result = analisar_retorno_raw(
        "nfeAutorizacaoLote",
        object(),
        b"<fake_post/>",
        FakeRetorno(response_rejeitada),
        retEnviNFe,
    )
    result.processo_xml = b"dummy"
    return result


def mocked_nfce_contingencia(*args, **kwargs):
    result = analisar_retorno_raw(
        "nfeAutorizacaoLote",
        object(),
        b"<fake_post/>",
        FakeRetorno(response_contingency),
        retEnviNFe,
    )
    result.processo_xml = b"dummy"
    return result


def mocked_inutilizacao(*args, **kwargs):
    result = analisar_retorno_raw(
        "nfeInutilizacaoNF",
        object(),
        b"<fake_post/>",
        FakeRetorno(response_inutilizacao),
        retInutNFe,
    )
    result.processo_xml = b"dummy"
    return result


def mock_cancela(*args, **kwargs):
    result = analisar_retorno_raw(
        "nfeRecepcaoEvento",
        object(),
        b"<fake_post/>",
        FakeRetorno(response_cancelamento),
        retEnvEvento,
    )
    result.processo_xml = b"dummy"
    return result


class TestNFCe(TestNFeExport):
    def setUp(self):
        super().setUp(nfe_list=[])

        self.document_id = self.env.ref("l10n_br_nfe.demo_nfce_same_state")

        certificate_valid = misc.create_fake_certificate_file(
            valid=True,
            passwd="123456",
            issuer="EMISSOR A TESTE",
            country="BR",
            subject="CERTIFICADO VALIDO TESTE",
        )
        certificate_id = self.env["l10n_br_fiscal.certificate"].create(
            {
                "type": "nf-e",
                "subtype": "a1",
                "password": "123456",
                "file": certificate_valid,
            }
        )
        self.document_id.company_id.certificate_nfe_id = certificate_id
        self.document_id.company_id.nfce_csc_token = "DUMMY"
        self.document_id.company_id.nfce_csc_code = "DUMMY"

        self.prepare_test_nfe(self.document_id)

    @mock.patch.object(DocumentoEletronico, "_post", side_effect=mocked_nfce_autorizada)
    def test_nfce_success(self, _mock_post):
        self.document_id.action_document_send()

        self.assertEqual(self.document_id.state_edoc, SITUACAO_EDOC_AUTORIZADA)

        cancel_wizard = (
            self.env["l10n_br_fiscal.document.cancel.wizard"]
            .with_context(
                active_model="l10n_br_fiscal.document", active_id=self.document_id.id
            )
            .create(
                {
                    "document_id": self.document_id.id,
                    "justification": "Era apenas um teste.",
                }
            )
        )
        with mock.patch.object(DocumentoEletronico, "_post", side_effect=mock_cancela):
            cancel_wizard.doit()

        self.assertEqual(self.document_id.state_edoc, SITUACAO_EDOC_CANCELADA)
        self.assertIsNotNone(self.document_id.cancel_event_id)
        self.assertEqual(self.document_id.cancel_event_id.state, "done")
        self.assertEqual(self.document_id.cancel_event_id.status_code, "101")
        self.assertEqual(
            self.document_id.cancel_event_id.response, "Era apenas um teste."
        )
        self.assertEqual(
            Datetime.to_string(self.document_id.cancel_event_id.protocol_date),
            "2023-07-05 16:52:52",
        )

    @mock.patch.object(DocumentoEletronico, "_post", side_effect=mocked_nfce_rejeitada)
    def test_nfce_rejeitada(self, _mock_post):
        self.document_id.action_document_send()
        self.assertEqual(self.document_id.state_edoc, SITUACAO_EDOC_REJEITADA)

    @mock.patch.object(DocumentoEletronico, "_post", side_effect=mocked_nfce_denegada)
    def test_nfce_denegada(self, _mock_post):
        self.document_id.action_document_send()
        self.assertEqual(self.document_id.state_edoc, SITUACAO_EDOC_DENEGADA)

    @mock.patch.object(
        DocumentoEletronico, "_post", side_effect=mocked_nfce_contingencia
    )
    def test_nfce_contingencia(self, _mock_post):
        self.document_id.action_document_send()
        self.assertEqual(self.document_id.state_edoc, SITUACAO_EDOC_A_ENVIAR)
        self.assertEqual(self.document_id.nfe_transmission, "9")

        self.assertIsNotNone(self.document_id.get_nfce_qrcode())

    @mock.patch.object(DocumentoEletronico, "_post", side_effect=mocked_inutilizacao)
    def test_inutilizar(self, mocked_post):
        inutilizar_wizard = (
            self.env["l10n_br_fiscal.invalidate.number.wizard"]
            .with_context(
                active_model="l10n_br_fiscal.document", active_id=self.document_id.id
            )
            .create(
                {
                    "document_id": self.document_id.id,
                    "justification": "Era apenas um teste.",
                }
            )
        )
        inutilizar_wizard.doit()

        self.assertEqual(self.document_id.state_edoc, SITUACAO_EDOC_INUTILIZADA)

    def test_atualiza_status_nfce(self):
        self.document_id._onchange_fiscal_operation_id()
        self.document_id._onchange_document_type_id()

        self.document_id._compute_nfe40_dhSaiEnt()
        self.assertFalse(self.document_id.nfe40_dhSaiEnt)

        self.document_id._inverse_nfe40_dhSaiEnt()
        self.assertFalse(self.document_id.nfe40_dhSaiEnt)

        mock_autorizada = mock.MagicMock(spec=["protocolo"])
        mock_autorizada.protocolo.infProt.cStat = AUTORIZADO[0]
        mock_autorizada.protocolo.infProt.xMotivo = "TESTE AUTORIZADO"
        mock_autorizada.protocolo.infProt.dhRecbto = datetime.now()
        mock_autorizada.processo_xml = b"dummy"
        self.document_id.atualiza_status_nfe(mock_autorizada)

        self.assertEqual(self.document_id.state_edoc, SITUACAO_EDOC_AUTORIZADA)
        self.assertEqual(self.document_id.status_code, AUTORIZADO[0])
        self.assertEqual(self.document_id.status_name, "TESTE AUTORIZADO")

    def test_qrcode(self):
        old_document_type = self.document_id.document_type_id
        self.document_id.document_type_id = False

        qr_code = self.document_id.get_nfce_qrcode()
        qr_code_url = self.document_id.get_nfce_qrcode_url()
        self.assertIsNone(qr_code)
        self.assertIsNone(qr_code_url)

        self.document_id.document_type_id = old_document_type
        qr_code = self.document_id.get_nfce_qrcode()
        qr_code_url = self.document_id.get_nfce_qrcode_url()
        self.assertIsNotNone(qr_code)
        self.assertIsNotNone(qr_code_url)

    @mock.patch.object(DocumentoEletronico, "_post", side_effect=mocked_nfce_autorizada)
    def test_prepare_nfce_payment(self, _mock):
        amount = self.document_id.amount_financial_total / 2
        self.document_id.nfe40_detPag = [
            (5, 0, 0),
            (
                0,
                0,
                {
                    "nfe40_indPag": "0",
                    "nfe40_tPag": "99",
                    "nfe40_vPag": amount,
                },
            ),
            (
                0,
                0,
                {
                    "nfe40_indPag": "0",
                    "nfe40_tPag": "99",
                    "nfe40_vPag": amount,
                },
            ),
        ]

        self.document_id._eletronic_document_send()

        others_pag = self.document_id.nfe40_detPag.filtered(
            lambda p: p.nfe40_tPag == "99"
        )
        self.assertTrue(all(pag.nfe40_xPag == "Outros" for pag in others_pag))

    def test_view_nfce_pdf(self):
        action_pdf = self.document_id.view_pdf()
        report_action = action_pdf["context"]["report_action"]

        self.assertEqual(report_action["report_file"], "l10n_br_nfe.danfe_nfce")
        self.assertEqual(report_action["report_name"], "l10n_br_nfe.report_danfe_nfce")
        self.assertEqual(report_action["report_type"], "qweb-html")

    def test_prepare_nfce_values_for_pdf(self):
        line_values = self.document_id._prepare_nfce_danfe_line_values()

        line1 = line_values[0]
        self.assertEqual(line1["product_quantity"], 1)
        self.assertEqual(line1["product_unit_value"], 320)
        self.assertEqual(line1["product_unit_total"], 320)

        self.document_id.nfe40_detPag = [
            (5, 0, 0),
            (
                0,
                0,
                {
                    "nfe40_indPag": "1",
                    "nfe40_tPag": "01",
                    "nfe40_vPag": 320,
                },
            ),
        ]

        payment_values = self.document_id._prepare_nfce_danfe_payment_values()
        payment = payment_values[0]

        self.assertEqual(payment["method"], "01 - Dinheiro")
        self.assertEqual(payment["value"], 320)

    def test_compute_fiscal_document_fields(self):
        self.document_id.partner_id.is_anonymous_consumer = True
        self.document_id.partner_id.cnpj_cpf = False
        self.document_id.partner_shipping_id = self.document_id.partner_id

        self.document_id._compute_entrega_data()
        self.assertFalse(self.document_id.nfe40_entrega)

        self.document_id._compute_dest_data()
        self.assertFalse(self.document_id.nfe40_dest)
