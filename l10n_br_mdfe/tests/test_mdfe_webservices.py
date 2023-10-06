# Copyright 2023 KMEE (Felipe Zago Rodrigues <felipe.zago@kmee.com.br>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
# pylint: disable=line-too-long

from datetime import datetime
from unittest import mock

from nfelib.mdfe.bindings.v3_0.ret_cons_reci_mdfe_v3_00 import RetConsReciMdfe
from nfelib.mdfe.bindings.v3_0.ret_evento_mdfe_v3_00 import RetEventoMdfe
from nfelib.nfe.ws.edoc_legacy import (
    DocumentoElectronicoAdapter as DocumentoEletronico,
    analisar_retorno_raw_xsdata,
)

from odoo.fields import Datetime

from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    AUTORIZADO,
    SITUACAO_EDOC_AUTORIZADA,
    SITUACAO_EDOC_CANCELADA,
    SITUACAO_EDOC_ENCERRADA,
    SITUACAO_EDOC_REJEITADA,
)

from .test_mdfe_serialize import TestMDFeSerialize

# flake8: noqa: B950
response_autorizada = """<?xml version="1.0" encoding="utf-8"?><soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema"><soap:Header><mdfeCabecMsg xmlns="http://www.portalfiscal.inf.br/mdfe/wsdl/MDFeRetRecepcao"><cUF>35</cUF><versaoDados>3.00</versaoDados></mdfeCabecMsg></soap:Header><soap:Body><mdfeRetRecepcaoResult xmlns="http://www.portalfiscal.inf.br/mdfe/wsdl/MDFeRetRecepcao"><retConsReciMDFe versao="3.00" xmlns="http://www.portalfiscal.inf.br/mdfe"><tpAmb>2</tpAmb><verAplic>RS20230517152856</verAplic><nRec>359000011934294</nRec><cStat>104</cStat><xMotivo>Arquivo processado</xMotivo><cUF>35</cUF><protMDFe versao="3.00"><infProt Id="MDFe935230000069676"><tpAmb>2</tpAmb><verAplic>RS20230517152856</verAplic><chMDFe>35231005472475000102580200000700031636764375</chMDFe><dhRecbto>2023-10-06T13:00:00-03:00</dhRecbto><nProt>935230000069676</nProt><digVal>MZn64O3kFyMQ+DEP79F3gt2F0PU=</digVal><cStat>100</cStat><xMotivo>Autorizado o uso do MDF-e</xMotivo></infProt></protMDFe></retConsReciMDFe></mdfeRetRecepcaoResult></soap:Body></soap:Envelope>"""

response_rejeitada = """<?xml version="1.0" encoding="utf-8"?><soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema"><soap:Header><mdfeCabecMsg xmlns="http://www.portalfiscal.inf.br/mdfe/wsdl/MDFeRetRecepcao"><cUF>35</cUF><versaoDados>3.00</versaoDados></mdfeCabecMsg></soap:Header><soap:Body><mdfeRetRecepcaoResult xmlns="http://www.portalfiscal.inf.br/mdfe/wsdl/MDFeRetRecepcao"><retConsReciMDFe versao="3.00" xmlns="http://www.portalfiscal.inf.br/mdfe"><tpAmb>2</tpAmb><verAplic>RS20230517152856</verAplic><nRec>359000011934276</nRec><cStat>104</cStat><xMotivo>Arquivo processado</xMotivo><cUF>35</cUF><protMDFe versao="3.00"><infProt Id="MDFe061020231333341980"><tpAmb>2</tpAmb><verAplic>RS20230517152856</verAplic><chMDFe>35231005472475000102580200000700021636572665</chMDFe><dhRecbto>2023-10-06T13:00:00-03:00</dhRecbto><cStat>204</cStat><xMotivo>Rejeição: Duplicidade de MDF-e  [nProt:935230000069668][dhAut:2023-10-06T13:00:00-03:00]</xMotivo></infProt></protMDFe></retConsReciMDFe></mdfeRetRecepcaoResult></soap:Body></soap:Envelope>"""

response_cancelamento = """<?xml version="1.0" encoding="utf-8"?><soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema"><soap:Header><mdfeCabecMsg xmlns="http://www.portalfiscal.inf.br/mdfe/wsdl/MDFeRecepcaoEvento"><cUF>35</cUF><versaoDados>3.00</versaoDados></mdfeCabecMsg></soap:Header><soap:Body><mdfeRecepcaoEventoResult xmlns="http://www.portalfiscal.inf.br/mdfe/wsdl/MDFeRecepcaoEvento"><retEventoMDFe xmlns="http://www.portalfiscal.inf.br/mdfe" versao="3.00"><infEvento Id="ID935230000069678"><tpAmb>2</tpAmb><verAplic>RS20230927085804</verAplic><cOrgao>35</cOrgao><cStat>135</cStat><xMotivo>Evento registrado e vinculado ao MDF-e</xMotivo><chMDFe>35231005472475000102580200000700041639188984</chMDFe><tpEvento>110111</tpEvento><xEvento>Cancelamento</xEvento><nSeqEvento>001</nSeqEvento><dhRegEvento>2023-10-06T13:00:00-03:00</dhRegEvento><nProt>935230000069678</nProt></infEvento></retEventoMDFe></mdfeRecepcaoEventoResult></soap:Body></soap:Envelope>"""

response_encerramento = """<?xml version="1.0" encoding="utf-8"?><soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema"><soap:Header><mdfeCabecMsg xmlns="http://www.portalfiscal.inf.br/mdfe/wsdl/MDFeRecepcaoEvento"><cUF>35</cUF><versaoDados>3.00</versaoDados></mdfeCabecMsg></soap:Header><soap:Body><mdfeRecepcaoEventoResult xmlns="http://www.portalfiscal.inf.br/mdfe/wsdl/MDFeRecepcaoEvento"><retEventoMDFe xmlns="http://www.portalfiscal.inf.br/mdfe" versao="3.00"><infEvento Id="ID935230000069680"><tpAmb>2</tpAmb><verAplic>RS20230927085804</verAplic><cOrgao>35</cOrgao><cStat>135</cStat><xMotivo>Evento registrado e vinculado ao MDF-e</xMotivo><chMDFe>35231005472475000102580200000700011636567559</chMDFe><tpEvento>110112</tpEvento><xEvento>Encerramento</xEvento><nSeqEvento>001</nSeqEvento><dhRegEvento>2023-10-06T13:00:00-03:00</dhRegEvento><nProt>935230000069680</nProt></infEvento></retEventoMDFe></mdfeRecepcaoEventoResult></soap:Body></soap:Envelope>"""


class FakeRetorno(object):
    def __init__(self, text):
        self.text = text
        self.content = text.encode("utf-8")

    def raise_for_status(self):
        pass


def mocked_mdfe_autorizada(*args, **kwargs):
    result = analisar_retorno_raw_xsdata(
        "nfeAutorizacaoLote",
        object(),
        b"<fake_post/>",
        FakeRetorno(response_autorizada),
        RetConsReciMdfe,
    )
    result.processo_xml = b"dummy"
    return result


def mocked_mdfe_rejeitada(*args, **kwargs):
    result = analisar_retorno_raw_xsdata(
        "nfeAutorizacaoLote",
        object(),
        b"<fake_post/>",
        FakeRetorno(response_rejeitada),
        RetConsReciMdfe,
    )
    result.processo_xml = b"dummy"
    return result


def mock_mdfe_cancelamento(*args, **kwargs):
    result = analisar_retorno_raw_xsdata(
        "nfeRecepcaoEvento",
        object(),
        b"<fake_post/>",
        FakeRetorno(response_cancelamento),
        RetEventoMdfe,
    )
    result.processo_xml = b"dummy"
    return result


def mock_mdfe_encerramento(*args, **kwargs):
    result = analisar_retorno_raw_xsdata(
        "nfeRecepcaoEvento",
        object(),
        b"<fake_post/>",
        FakeRetorno(response_encerramento),
        RetEventoMdfe,
    )
    result.processo_xml = b"dummy"
    return result


class TestMDFeWebServices(TestMDFeSerialize):
    def setUp(self):
        super().setUp(mdfe_list=[])

        self.sn_company_id.district = "TEST"
        self.sn_company_id.street2 = "TEST"

        self.document_id = self.env["l10n_br_fiscal.document"].create(
            self._get_default_document_data()
        )
        self.prepare_test_mdfe(self.document_id)

    @mock.patch.object(DocumentoEletronico, "_post", side_effect=mocked_mdfe_autorizada)
    def test_mdfe_success(self, _mock_post):
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
        with mock.patch.object(
            DocumentoEletronico, "_post", side_effect=mock_mdfe_cancelamento
        ):
            cancel_wizard.doit()

        self.assertEqual(self.document_id.state_edoc, SITUACAO_EDOC_CANCELADA)
        self.assertIsNotNone(self.document_id.cancel_event_id)
        self.assertEqual(self.document_id.cancel_event_id.state, "done")
        self.assertEqual(self.document_id.cancel_event_id.status_code, "135")
        self.assertEqual(
            Datetime.to_string(self.document_id.cancel_event_id.protocol_date),
            "2023-10-06 13:00:00",
        )

    @mock.patch.object(DocumentoEletronico, "_post", side_effect=mocked_mdfe_rejeitada)
    def test_mdfe_rejeitada(self, _mock_post):
        self.document_id.action_document_send()
        self.assertEqual(self.document_id.state_edoc, SITUACAO_EDOC_REJEITADA)

    @mock.patch.object(DocumentoEletronico, "_post", side_effect=mocked_mdfe_autorizada)
    def test_encerramento_mdfe(self, _mock_post):
        self.document_id.action_document_send()

        closure_wizard = (
            self.env["l10n_br_fiscal.document.closure.wizard"]
            .with_context(
                active_model="l10n_br_fiscal.document", active_id=self.document_id.id
            )
            .create(
                {
                    "document_id": self.document_id.id,
                    "company_id": self.sn_company_id.id,
                    "state_id": self.acre_state.id,
                    "city_id": self.acre_city.id,
                }
            )
        )
        with mock.patch.object(
            DocumentoEletronico, "_post", side_effect=mock_mdfe_encerramento
        ):
            closure_wizard.doit()

        self.assertEqual(self.document_id.state_edoc, SITUACAO_EDOC_ENCERRADA)
        self.assertIsNotNone(self.document_id.closure_event_id)
        self.assertEqual(self.document_id.closure_event_id.state, "done")
        self.assertEqual(self.document_id.closure_event_id.status_code, "135")
        self.assertEqual(
            Datetime.to_string(self.document_id.closure_event_id.protocol_date),
            "2023-10-06 13:00:00",
        )

    def test_atualiza_status_mdfe(self):
        mock_autorizada = mock.MagicMock(spec=["resposta"])
        mock_autorizada.resposta.protMDFe.infProt.cStat = AUTORIZADO[0]
        mock_autorizada.resposta.protMDFe.infProt.xMotivo = "TESTE AUTORIZADO"
        mock_autorizada.resposta.protMDFe.infProt.dhRecbto = datetime.now()
        mock_autorizada.processo_xml = b"dummy"
        self.document_id.atualiza_status_mdfe(mock_autorizada)

        self.assertEqual(self.document_id.state_edoc, SITUACAO_EDOC_AUTORIZADA)
        self.assertEqual(self.document_id.status_code, AUTORIZADO[0])
        self.assertEqual(self.document_id.status_name, "TESTE AUTORIZADO")

    def test_qrcode(self):
        old_document_type = self.document_id.document_type_id
        self.document_id.document_type_id = False

        qr_code = self.document_id.get_mdfe_qrcode()
        self.assertIsNone(qr_code)

        self.document_id.document_type_id = old_document_type
        qr_code = self.document_id.get_mdfe_qrcode()
        self.assertIsNotNone(qr_code)
