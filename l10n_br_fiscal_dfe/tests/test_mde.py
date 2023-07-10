# Copyright (C) 2023 - TODAY Felipe Zago - KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
# pylint: disable=line-too-long

from unittest import mock

from erpbrasil.edoc.resposta import analisar_retorno_raw
from nfelib.nfe.ws.edoc_legacy import DocumentoElectronicoAdapter
from nfelib.v4_00 import retEnvEvento

from odoo.tests.common import TransactionCase

from ..models.mde.mde import MDe
from .test_dfe import mocked_post_success

# flake8: noqa: B950
response_confirmacao_operacao = """<?xml version="1.0" encoding="UTF-8"?><soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"><soap:Body><nfeResultMsg xmlns="http://www.portalfiscal.inf.br/nfe/wsdl/NFeRecepcaoEvento4"><retEnvEvento xmlns="http://www.portalfiscal.inf.br/nfe" versao="1.00"><idLote /><tpAmb>2</tpAmb><verAplic>SVRS202305251555</verAplic><cStat>135</cStat><retEvento versao="1.00"><infEvento><tpAmb>2</tpAmb><verAplic>SVRS202305251555</verAplic><cStat>135</cStat><xMotivo>Teste Confirmação da Operação.</xMotivo><chNFe>31201010588201000105550010038421171838422178</chNFe><tpEvento>210200</tpEvento><xEvento>Confirmacao de Operacao registrada</xEvento><nSeqEvento>1</nSeqEvento><CNPJDest>81583054000129</CNPJDest><dhRegEvento>2023-07-10T10:00:00-03:00</dhRegEvento></infEvento></retEvento></retEnvEvento></nfeResultMsg></soap:Body></soap:Envelope>"""

response_ciencia_operacao = """<?xml version="1.0" encoding="UTF-8"?><soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"><soap:Body><nfeResultMsg xmlns="http://www.portalfiscal.inf.br/nfe/wsdl/NFeRecepcaoEvento4"><retEnvEvento xmlns="http://www.portalfiscal.inf.br/nfe" versao="1.00"><idLote /><tpAmb>2</tpAmb><verAplic>SVRS202305251555</verAplic><cStat>135</cStat><retEvento versao="1.00"><infEvento><tpAmb>2</tpAmb><verAplic>SVRS202305251555</verAplic><cStat>135</cStat><xMotivo>Teste Ciência da Operação.</xMotivo><chNFe>31201010588201000105550010038421171838422178</chNFe><tpEvento>210210</tpEvento><xEvento>Ciencia da Operacao registrada</xEvento><nSeqEvento>1</nSeqEvento><CNPJDest>81583054000129</CNPJDest><dhRegEvento>2023-07-10T10:00:00-03:00</dhRegEvento></infEvento></retEvento></retEnvEvento></nfeResultMsg></soap:Body></soap:Envelope>"""

response_desconhecimento_operacao = """<?xml version="1.0" encoding="UTF-8"?><soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"><soap:Body><nfeResultMsg xmlns="http://www.portalfiscal.inf.br/nfe/wsdl/NFeRecepcaoEvento4"><retEnvEvento xmlns="http://www.portalfiscal.inf.br/nfe" versao="1.00"><idLote /><tpAmb>2</tpAmb><verAplic>SVRS202305251555</verAplic><cStat>135</cStat><retEvento versao="1.00"><infEvento><tpAmb>2</tpAmb><verAplic>SVRS202305251555</verAplic><cStat>135</cStat><xMotivo>Teste Desconhecimento da Operação.</xMotivo><chNFe>31201010588201000105550010038421171838422178</chNFe><tpEvento>210220</tpEvento><xEvento>Desconhecimento da Operacao registrada</xEvento><nSeqEvento>1</nSeqEvento><CNPJDest>81583054000129</CNPJDest><dhRegEvento>2023-07-10T10:00:00-03:00</dhRegEvento></infEvento></retEvento></retEnvEvento></nfeResultMsg></soap:Body></soap:Envelope>"""

response_operacao_nao_realizada = """<?xml version="1.0" encoding="UTF-8"?><soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"><soap:Body><nfeResultMsg xmlns="http://www.portalfiscal.inf.br/nfe/wsdl/NFeRecepcaoEvento4"><retEnvEvento xmlns="http://www.portalfiscal.inf.br/nfe" versao="1.00"><idLote /><tpAmb>2</tpAmb><verAplic>SVRS202305251555</verAplic><cStat>135</cStat><retEvento versao="1.00"><infEvento><tpAmb>2</tpAmb><verAplic>SVRS202305251555</verAplic><cStat>135</cStat><xMotivo>Teste Operação não Realizada.</xMotivo><chNFe>31201010588201000105550010038421171838422178</chNFe><tpEvento>210240</tpEvento><xEvento>Operacao nao Realizada registrada</xEvento><nSeqEvento>1</nSeqEvento><CNPJDest>81583054000129</CNPJDest><dhRegEvento>2023-07-10T10:00:00-03:00</dhRegEvento></infEvento></retEvento></retEnvEvento></nfeResultMsg></soap:Body></soap:Envelope>"""


class FakeRetorno(object):
    def __init__(self, text, status_code="200"):
        self.text = text
        self.content = text.encode("utf-8")
        self.status_code = status_code

    def raise_for_status(self):
        pass


def mocked_post_confirmacao(*args, **kwargs):
    return analisar_retorno_raw(
        "nfeRecepcaoEvento",
        object(),
        b"<fake_post/>",
        FakeRetorno(response_confirmacao_operacao),
        retEnvEvento,
    )


def mocked_post_ciencia(*args, **kwargs):
    return analisar_retorno_raw(
        "nfeRecepcaoEvento",
        object(),
        b"<fake_post/>",
        FakeRetorno(response_ciencia_operacao),
        retEnvEvento,
    )


def mocked_post_desconhecimento(*args, **kwargs):
    return analisar_retorno_raw(
        "nfeRecepcaoEvento",
        object(),
        b"<fake_post/>",
        FakeRetorno(response_desconhecimento_operacao),
        retEnvEvento,
    )


def mocked_post_nao_realizada(*args, **kwargs):
    return analisar_retorno_raw(
        "nfeRecepcaoEvento",
        object(),
        b"<fake_post/>",
        FakeRetorno(response_operacao_nao_realizada),
        retEnvEvento,
    )


class TestNFeWebservices(TransactionCase):
    def setUp(self):
        super().setUp()

        self.dfe_id = self.env["l10n_br_fiscal.dfe"].create(
            {"company_id": self.env.ref("l10n_br_base.empresa_lucro_presumido").id}
        )

        with mock.patch.object(
            DocumentoElectronicoAdapter,
            "_post",
            side_effect=mocked_post_success,
        ):
            self.dfe_id.search_documents()

        self.mde_id = self.dfe_id.imported_mde_ids[0]

    def test_events_success(self):
        with mock.patch.object(
            DocumentoElectronicoAdapter,
            "_post",
            side_effect=mocked_post_confirmacao,
        ):
            self.mde_id.action_confirmar_operacacao()
            self.assertEqual(self.mde_id.state, "confirmado")

        with mock.patch.object(
            DocumentoElectronicoAdapter,
            "_post",
            side_effect=mocked_post_ciencia,
        ):
            self.mde_id.action_ciencia_emissao()
            self.assertEqual(self.mde_id.state, "ciente")

        with mock.patch.object(
            DocumentoElectronicoAdapter,
            "_post",
            side_effect=mocked_post_desconhecimento,
        ):
            self.mde_id.action_operacao_desconhecida()
            self.assertEqual(self.mde_id.state, "desconhecido")

        with mock.patch.object(
            DocumentoElectronicoAdapter,
            "_post",
            side_effect=mocked_post_nao_realizada,
        ):
            self.mde_id.action_negar_operacao()
            self.assertEqual(self.mde_id.state, "nao_realizado")

    @mock.patch.object(
        DocumentoElectronicoAdapter,
        "_post",
        side_effect=mocked_post_success,
    )
    @mock.patch.object(MDe, "action_ciencia_emissao", return_value=None)
    def test_download_documents(self, _mock_post, _mock_ciencia):
        mde_ids = self.mde_id + self.mde_id.copy()

        result_single = self.mde_id.action_download_all_xmls()
        result_multiple = mde_ids.action_download_all_xmls()

        attachment_single = self.get_attachment_from_result(result_single)
        attachment_multiple = self.get_attachment_from_result(result_multiple)

        self.assertTrue(attachment_single)
        self.assertEqual(attachment_single.name, f"NFe{self.mde_id.key}.xml")

        self.assertTrue(attachment_multiple)
        self.assertEqual(attachment_multiple.name, f"attachments.tar.gz")

    def get_attachment_from_result(self, result):
        _, _, _, att_id, _ = result["url"].split("/")
        return self.env["ir.attachment"].browse(int(att_id))
