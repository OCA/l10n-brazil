# Copyright (C) 2023 - TODAY Raphaël Valyi - Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
# pylint: disable=line-too-long

import logging
import subprocess
from unittest import mock

from erpbrasil.edoc.resposta import analisar_retorno_raw
from lxml import etree
from nfelib.nfe.ws.edoc_legacy import DocumentoElectronicoAdapter as DocumentoEletronico
from nfelib.v4_00 import (
    retConsReciNFe,
    retConsStatServ,
    retEnvEvento,
    retEnviNFe,
    retInutNFe,
)

from odoo.fields import Datetime

from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    SITUACAO_EDOC_AUTORIZADA,
    SITUACAO_EDOC_CANCELADA,
)
from odoo.addons.l10n_br_nfe.models.document import NFe

from .test_nfe_serialize import TestNFeExport

_logger = logging.getLogger(__name__)

# flake8: noqa: B950
response_status = """<?xml version="1.0" encoding="utf-8"?><soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema"><soap:Body><nfeResultMsg xmlns="http://www.portalfiscal.inf.br/nfe/wsdl/NFeStatusServico4"><retConsStatServ versao="4.00" xmlns="http://www.portalfiscal.inf.br/nfe"><tpAmb>2</tpAmb><verAplic>SVRS202305251555</verAplic><cStat>107</cStat><xMotivo>Servico em Operacao</xMotivo><cUF>42</cUF><dhRecbto>2023-06-11T00:15:00-03:00</dhRecbto><tMed>1</tMed></retConsStatServ></nfeResultMsg></soap:Body></soap:Envelope>"""

response_envia_documento = """<?xml version="1.0" encoding="utf-8"?><soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema"><soap:Body><nfeResultMsg xmlns="http://www.portalfiscal.inf.br/nfe/wsdl/NFeAutorizacao4"><retEnviNFe versao="4.00" xmlns="http://www.portalfiscal.inf.br/nfe"><tpAmb>2</tpAmb><verAplic>SVRS202305251555</verAplic><cStat>103</cStat><xMotivo>Lote recebido com sucesso</xMotivo><cUF>42</cUF><dhRecbto>2023-06-11T01:18:19-03:00</dhRecbto><infRec><nRec>423002202113232</nRec><tMed>1</tMed></infRec></retEnviNFe></nfeResultMsg></soap:Body></soap:Envelope>"""

response_consulta_documento = """<?xml version="1.0" encoding="utf-8"?><soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema"><soap:Body><nfeResultMsg xmlns="http://www.portalfiscal.inf.br/nfe/wsdl/NFeConsultaProtocolo4"><retConsSitNFe versao="4.00" xmlns="http://www.portalfiscal.inf.br/nfe"><tpAmb>2</tpAmb><verAplic>SVRS202305251555</verAplic><cStat>217</cStat><xMotivo>Rejeicao: NF-e nao consta na base de dados da SEFAZ</xMotivo><cUF>42</cUF><dhRecbto>2023-06-11T01:20:55-03:00</dhRecbto><chNFe>42230675277525000259550010000364481754015406</chNFe></retConsSitNFe></nfeResultMsg></soap:Body></soap:Envelope>"""

response_consulta_recibo = """<?xml version="1.0" encoding="utf-8"?><soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema"><soap:Body><nfeResultMsg xmlns="http://www.portalfiscal.inf.br/nfe/wsdl/NFeRetAutorizacao4"><retConsReciNFe versao="4.00" xmlns="http://www.portalfiscal.inf.br/nfe"><tpAmb>2</tpAmb><verAplic>SVRS202305261028</verAplic><nRec>423002202113232</nRec><cStat>100</cStat><xMotivo>Lote processado</xMotivo><cUF>42</cUF><dhRecbto>2023-06-11T01:18:19-03:00</dhRecbto><protNFe versao="4.00"><infProt><tpAmb>2</tpAmb><verAplic>SVRS202304261131</verAplic><chNFe>35200159594315000157550010000000022062777169</chNFe><dhRecbto>2023-06-02T10:47:21-03:00</dhRecbto><nProt>423002202113232</nProt><digVal>IoYUWXt2fIiRXb7UYRgl77c6Zlk=</digVal><cStat>100</cStat><xMotivo>Autorizado o uso da NF-e</xMotivo></infProt></protNFe></retConsReciNFe></nfeResultMsg></soap:Body></soap:Envelope>"""

response_cancela_documento = """<?xml version="1.0" encoding="UTF-8"?><soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"><soap:Body><nfeResultMsg xmlns="http://www.portalfiscal.inf.br/nfe/wsdl/NFeRecepcaoEvento4"><retEnvEvento xmlns="http://www.portalfiscal.inf.br/nfe" versao="1.00"><idLote /><tpAmb>2</tpAmb><verAplic>SVRS202305251555</verAplic><cStat>101</cStat><retEvento versao="1.00"><infEvento><tpAmb>2</tpAmb><verAplic>SVRS202305251555</verAplic><cStat>101</cStat><xMotivo>Era apenas um teste.</xMotivo><chNFe>35200159594315000157550010000000022062777169</chNFe><tpEvento>110111</tpEvento><xEvento>Cancelamento registrado</xEvento><nSeqEvento>1</nSeqEvento><CNPJDest>81583054000129</CNPJDest><dhRegEvento>2023-07-05T16:52:52-03:00</dhRegEvento></infEvento></retEvento></retEnvEvento></nfeResultMsg></soap:Body></soap:Envelope>"""

response_inutilizacao = """<?xml version="1.0" encoding="utf-8"?><soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema"><soap:Body><nfeResultMsg xmlns="http://www.portalfiscal.inf.br/nfe/wsdl/NFeInutilizacao4"><retInutNFe versao="4.00" xmlns="http://www.portalfiscal.inf.br/nfe"><infInut><tpAmb>2</tpAmb><verAplic>SVRS202305251555</verAplic><cStat>102</cStat><cUF>42</cUF><ano>23</ano><CNPJ>81583054000129</CNPJ><mod>55</mod><serie>1</serie><nNFIni>2</nNFIni><nNFFin>2</nNFFin><dhRecbto>2023-06-15T21:50:40-03:00</dhRecbto></infInut></retInutNFe></nfeResultMsg></soap:Body></soap:Envelope>"""


def is_libreoffice_command_available():
    try:
        subprocess.run(["libreoffice", "--version"], check=True)
        return True
    except subprocess.CalledProcessError:
        return False
    except FileNotFoundError:
        return False


class FakeRetorno(object):
    def __init__(self, text):
        self.text = text
        self.content = text.encode("utf-8")

    def raise_for_status(self):
        pass


def mocked_post(*args, **kwargs):
    if args[2] == "nfeStatusServicoNF":
        fake_retorno = FakeRetorno(response_status)
        return analisar_retorno_raw(
            "nfeStatusServicoNF",
            object(),
            b"<fake_post/>",
            fake_retorno,
            retConsStatServ,
        )

    elif args[2] == "nfeConsultaNF":
        fake_retorno = FakeRetorno(response_consulta_documento)
        return analisar_retorno_raw(
            "nfeConsultaNF",
            object(),
            b"<fake_post/>",
            fake_retorno,
            retConsReciNFe,
        )

    elif args[2] == "nfeAutorizacaoLote":
        fake_retorno = FakeRetorno(response_envia_documento)
        nfe_etree = args[0][2]
        nfe = (
            etree.tostring(nfe_etree)
            .decode("utf-8")
            .replace(' xmlns="http://www.portalfiscal.inf.br/nfe"', "")
        )
        FakeRetorno.nfe = nfe
        envi_nfe = (
            '<enviNFe xmlns="http://www.portalfiscal.inf.br/nfe" versao="4.00">%s</enviNFe>'
            % (nfe,)
        )
        return analisar_retorno_raw(
            "nfeAutorizacaoLote",
            etree.fromstring(envi_nfe),
            b"<fake_post/>",
            fake_retorno,
            retEnviNFe,
        )

    elif args[2] == "nfeRetAutorizacaoLote":
        fake_retorno = FakeRetorno(response_consulta_recibo)
        nfe = FakeRetorno.nfe
        return analisar_retorno_raw(
            "nfeAutorizacaoLote",
            object(),
            nfe.encode("utf-8"),
            fake_retorno,
            retConsReciNFe,
        )

    elif args[2] == "nfeRecepcaoEvento":
        fake_retorno = FakeRetorno(response_cancela_documento)
        nfe = FakeRetorno.nfe
        return analisar_retorno_raw(
            "nfeRecepcaoEvento",
            object(),
            nfe.encode("utf-8"),
            fake_retorno,
            retEnvEvento,
        )

    elif args[2] == "nfeInutilizacaoNF":
        fake_retorno = FakeRetorno(response_inutilizacao)
        return analisar_retorno_raw(
            "nfeInutilizacaoNF",
            object(),
            b"<fake_post/>",
            fake_retorno,
            retInutNFe,
        )


class TestNFeWebservices(TestNFeExport):
    def setUp(self):
        nfe_list = [
            {
                "record_ref": "l10n_br_nfe.demo_nfe_natural_icms_18_red_51_11",
                "xml_file": "NFe35200159594315000157550010000000022062777169.xml",
            },
        ]
        super().setUp(nfe_list)

    @mock.patch.object(DocumentoEletronico, "_post", side_effect=mocked_post)
    def test_enviar_e_cancelar(self, _mock_post):
        for nfe_data in self.nfe_list:
            nfe = nfe_data["nfe"]

            if not is_libreoffice_command_available():
                with mock.patch.object(NFe, "make_pdf"):
                    nfe.action_document_send()
            else:
                # testing with the original make_pdf requires you have
                # apt-get install locale
                # locale-gen pt_BR.UTF-8
                # dpkg-reconfigure locales
                # pip install "reportlab==3.5.54"
                # apt-get install libreoffice
                nfe.action_document_send()

            self.assertEqual(nfe.state_edoc, SITUACAO_EDOC_AUTORIZADA)

            cancel_wizard = (
                self.env["l10n_br_fiscal.document.cancel.wizard"]
                .with_context(active_model="l10n_br_fiscal.document", active_id=nfe.id)
                .create(
                    {"document_id": nfe.id, "justification": "Era apenas um teste."}
                )
            )
            cancel_wizard.doit()

            self.assertEqual(nfe.state_edoc, SITUACAO_EDOC_CANCELADA)
            self.assertIsNotNone(nfe.cancel_event_id)
            self.assertEqual(nfe.cancel_event_id.state, "done")
            self.assertEqual(nfe.cancel_event_id.status_code, "101")
            self.assertEqual(nfe.cancel_event_id.response, "Era apenas um teste.")
            self.assertEqual(
                Datetime.to_string(nfe.cancel_event_id.protocol_date),
                "2023-07-05 16:52:52",
            )

    @mock.patch.object(DocumentoEletronico, "_post", side_effect=mocked_post)
    def test_inutilizar(self, mocked_post):
        nfe = self.nfe_list[0]["nfe"]
        inutilizar_wizard = (
            self.env["l10n_br_fiscal.invalidate.number.wizard"]
            .with_context(active_model="l10n_br_fiscal.document", active_id=nfe.id)
            .create({"document_id": nfe.id, "justification": "Era apenas um teste."})
        )
        inutilizar_wizard.doit()
